"""
SEC HTTP Client with rate limiting, caching, and fair access compliance.

This module provides a shared HTTP client for all SEC tools that:
- Enforces <= 10 requests/second rate limit
- Implements caching for JSON responses and downloads
- Sends proper User-Agent headers
- Handles retries and errors gracefully
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from collections import deque
import hashlib
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RateLimiter:
    """Simple rate limiter that enforces max requests per second."""
    
    def __init__(self, max_requests_per_second: float = 10.0):
        self.max_rps = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.request_times: deque = deque()
    
    def wait_if_needed(self):
        """Wait if necessary to maintain rate limit."""
        now = time.time()
        
        # Remove timestamps older than 1 second
        while self.request_times and now - self.request_times[0] > 1.0:
            self.request_times.popleft()
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.max_rps:
            sleep_time = 1.0 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                now = time.time()
                # Clean up again after sleep
                while self.request_times and now - self.request_times[0] > 1.0:
                    self.request_times.popleft()
        
        # Record this request
        self.request_times.append(now)


class SimpleCache:
    """Simple file-based cache with TTL support."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".sec_tools_cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check if expired
            if time.time() > cached.get('expires_at', 0):
                cache_path.unlink()  # Delete expired cache
                return None
            
            return cached.get('value')
        except (json.JSONDecodeError, IOError):
            # Corrupted cache file, delete it
            cache_path.unlink()
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Cache a value with TTL."""
        cache_path = self._get_cache_path(key)
        try:
            cached = {
                'value': value,
                'expires_at': time.time() + ttl_seconds
            }
            with open(cache_path, 'w') as f:
                json.dump(cached, f)
        except IOError:
            # If we can't write cache, just continue without caching
            pass


class SECHttpClient:
    """
    HTTP client for SEC APIs with rate limiting, caching, and fair access compliance.
    
    Usage:
        client = SECHttpClient()
        response = client.get("https://data.sec.gov/submissions/CIK0000789019.json")
    """
    
    def __init__(
        self,
        user_agent: str = "flow_researcher bryan@example.com",
        max_requests_per_second: float = 10.0,
        timeout: int = 30,
        cache_ttl_seconds: int = 3600,
        enable_cache: bool = True
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.cache_ttl = cache_ttl_seconds
        self.enable_cache = enable_cache
        
        # Setup rate limiter
        self.rate_limiter = RateLimiter(max_requests_per_second)
        
        # Setup cache
        self.cache = SimpleCache() if enable_cache else None
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/html, */*',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> requests.Response:
        """
        Perform a GET request with rate limiting and caching.
        
        Args:
            url: URL to fetch
            headers: Additional headers (merged with defaults)
            params: Query parameters
            use_cache: Whether to use cache for this request
        
        Returns:
            requests.Response object
        """
        # Check cache first
        if use_cache and self.cache:
            cache_key = f"{url}?{json.dumps(params or {}, sort_keys=True)}"
            cached_response = self.cache.get(cache_key)
            if cached_response is not None:
                # Create a mock response from cached data
                response = requests.Response()
                response.status_code = 200
                response._content = json.dumps(cached_response).encode()
                response.headers['Content-Type'] = 'application/json'
                return response
        
        # Rate limit
        self.rate_limiter.wait_if_needed()
        
        # Prepare headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Make request
        try:
            response = self.session.get(
                url,
                headers=request_headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Cache successful JSON responses
            if use_cache and self.cache and response.status_code == 200:
                try:
                    # Try to parse as JSON
                    json_data = response.json()
                    cache_key = f"{url}?{json.dumps(params or {}, sort_keys=True)}"
                    self.cache.set(cache_key, json_data, self.cache_ttl)
                except (json.JSONDecodeError, ValueError):
                    # Not JSON, don't cache
                    pass
            
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def download(
        self,
        url: str,
        dest_path: str,
        use_cache: bool = True
    ) -> str:
        """
        Download a file from SEC archives.
        
        Args:
            url: URL to download
            dest_path: Local path to save file
            use_cache: Check if file already exists locally
        
        Returns:
            Path to downloaded file
        """
        dest_path_obj = Path(dest_path)
        
        # Check if file already exists (simple cache check)
        if use_cache and dest_path_obj.exists():
            return str(dest_path_obj.absolute())
        
        # Ensure parent directory exists
        dest_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Rate limit
        self.rate_limiter.wait_if_needed()
        
        # Download file
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            with open(dest_path_obj, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(dest_path_obj.absolute())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {e}")


# Global client instance (can be overridden if needed)
_default_client: Optional[SECHttpClient] = None


def get_default_client() -> SECHttpClient:
    """Get or create the default SEC HTTP client."""
    global _default_client
    if _default_client is None:
        _default_client = SECHttpClient()
    return _default_client


def set_default_client(client: SECHttpClient):
    """Set a custom default client."""
    global _default_client
    _default_client = client
