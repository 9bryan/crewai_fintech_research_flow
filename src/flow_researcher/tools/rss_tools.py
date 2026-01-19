"""
RSS / "Latest Filings" Monitoring Tools.

These tools work with SEC RSS feeds for monitoring latest filings.
"""

import json
import re
from typing import Type, Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client


class GetCompanyEdgarRssFeedUrlInput(BaseModel):
    """Input schema for get_company_edgar_rss_feed_url tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")


class GetCompanyEdgarRssFeedUrlTool(BaseTool):
    """
    Get company EDGAR RSS feed URL.
    
    Constructs the RSS feed URL for a company's filings. The RSS feed
    provides updates when new filings are submitted.
    """
    name: str = "get_company_edgar_rss_feed_url"
    description: str = """
    Gets the RSS feed URL for a company's EDGAR filings. The RSS feed provides
    updates when new filings are submitted. URL format:
    https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=&dateb=&owner=exclude&count=40&output=atom
    """
    args_schema: Type[BaseModel] = GetCompanyEdgarRssFeedUrlInput

    def _run(self, cik: str) -> str:
        cik_padded = cik.strip().zfill(10)
        # Remove leading zeros for RSS feed URL
        cik_numeric = str(int(cik_padded))
        
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_numeric}&type=&dateb=&owner=exclude&count=40&output=atom"
        
        result = {
            "data": {
                "url": url,
                "cik": cik_padded,
                "format": "atom"
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)


class FetchRssInput(BaseModel):
    """Input schema for fetch_rss tool."""
    url: str = Field(..., description="RSS feed URL")


class FetchRssTool(BaseTool):
    """
    Fetch and parse RSS feed.
    
    Fetches an RSS/Atom feed and parses it into items with title, link,
    publication date, and description.
    """
    name: str = "fetch_rss"
    description: str = """
    Fetches and parses an RSS/Atom feed. Returns parsed items with title,
    link, publication date (pubDate), and description. Works with SEC EDGAR
    RSS feeds and other standard RSS/Atom feeds.
    """
    args_schema: Type[BaseModel] = FetchRssInput

    def _run(self, url: str) -> str:
        client = get_default_client()
        
        try:
            response = client.get(url)
            content = response.text
            
            # Parse RSS/Atom feed (simple parsing)
            items = []
            
            # Try Atom format first (SEC uses Atom)
            if '<?xml' in content and 'feed' in content:
                # Atom format
                entry_pattern = r'<entry[^>]*>(.*?)</entry>'
                entries = re.finditer(entry_pattern, content, re.DOTALL)
                
                for entry in entries:
                    entry_text = entry.group(1)
                    
                    # Extract title
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', entry_text, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else ""
                    
                    # Extract link
                    link_match = re.search(r'<link[^>]*href="([^"]+)"', entry_text)
                    link = link_match.group(1) if link_match else ""
                    
                    # Extract published date
                    pub_match = re.search(r'<published[^>]*>(.*?)</published>', entry_text)
                    pub_date = pub_match.group(1).strip() if pub_match else ""
                    
                    # Extract summary/description
                    summary_match = re.search(r'<summary[^>]*>(.*?)</summary>', entry_text, re.DOTALL)
                    description = summary_match.group(1).strip() if summary_match else ""
                    
                    items.append({
                        "title": title,
                        "link": link,
                        "pubDate": pub_date,
                        "description": description
                    })
            
            # Try RSS format
            elif '<rss' in content or '<rdf:RDF' in content:
                item_pattern = r'<item[^>]*>(.*?)</item>'
                rss_items = re.finditer(item_pattern, content, re.DOTALL)
                
                for item in rss_items:
                    item_text = item.group(1)
                    
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', item_text, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else ""
                    
                    link_match = re.search(r'<link[^>]*>(.*?)</link>', item_text)
                    link = link_match.group(1).strip() if link_match else ""
                    
                    pub_match = re.search(r'<pubDate[^>]*>(.*?)</pubDate>', item_text)
                    pub_date = pub_match.group(1).strip() if pub_match else ""
                    
                    desc_match = re.search(r'<description[^>]*>(.*?)</description>', item_text, re.DOTALL)
                    description = desc_match.group(1).strip() if desc_match else ""
                    
                    items.append({
                        "title": title,
                        "link": link,
                        "pubDate": pub_date,
                        "description": description
                    })
            
            result = {
                "data": {
                    "items": items,
                    "count": len(items)
                },
                "source_urls": [url],
                "warnings": [] if items else ["No items found in RSS feed or unsupported format"]
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": {"items": [], "count": 0},
                "source_urls": [url],
                "warnings": [f"Failed to fetch or parse RSS feed: {str(e)}"]
            })


class RssItemsToFilingsInput(BaseModel):
    """Input schema for rss_items_to_filings tool."""
    items: str = Field(
        ...,
        description="JSON string of RSS items from fetch_rss tool"
    )


class RssItemsToFilingsTool(BaseTool):
    """
    Extract filing information from RSS items.
    
    Extracts accession number, form type, and CIK from RSS feed items
    when possible.
    """
    name: str = "rss_items_to_filings"
    description: str = """
    Extracts filing information (accession number, form type, CIK) from
    RSS feed items when possible. Parses links and descriptions to extract
    filing metadata.
    """
    args_schema: Type[BaseModel] = RssItemsToFilingsInput

    def _run(self, items: str) -> str:
        try:
            if isinstance(items, str):
                data = json.loads(items)
            else:
                data = items
            
            # Extract items from data structure
            if isinstance(data, dict) and "data" in data:
                items_list = data["data"].get("items", [])
            elif isinstance(data, dict) and "items" in data:
                items_list = data["items"]
            elif isinstance(data, list):
                items_list = data
            else:
                items_list = []
            
            filings = []
            for item in items_list:
                link = item.get("link", "")
                title = item.get("title", "")
                description = item.get("description", "")
                
                # Try to extract accession number from link
                # Pattern: /Archives/edgar/data/{CIK}/{ACCESSION}/
                accn_match = re.search(r'/Archives/edgar/data/(\d+)/([^/]+)/', link)
                cik = None
                accession = None
                
                if accn_match:
                    cik = accn_match.group(1).zfill(10)
                    accession = accn_match.group(2)
                
                # Try to extract form type from title or description
                form = None
                for form_type in ["10-Q", "10-K", "8-K", "20-F", "6-K", "DEF 14A", "S-1"]:
                    if form_type in title or form_type in description:
                        form = form_type
                        break
                
                if cik or accession or form:
                    filings.append({
                        "cik": cik,
                        "accession": accession,
                        "form": form,
                        "title": title,
                        "link": link,
                        "pubDate": item.get("pubDate")
                    })
            
            result = {
                "data": {
                    "filings": filings,
                    "count": len(filings)
                },
                "source_urls": [],
                "warnings": [] if filings else ["No filing information extracted from RSS items"]
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": {"filings": [], "count": 0},
                "source_urls": [],
                "warnings": ["Invalid JSON in items parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": {"filings": [], "count": 0},
                "source_urls": [],
                "warnings": [f"Failed to extract filings from RSS items: {str(e)}"]
            })
