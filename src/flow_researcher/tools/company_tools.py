"""
Company Identity & Lookup Tools for SEC data.

These tools help identify companies by ticker, convert to CIK,
and retrieve company submissions and profiles.
"""

import json
from typing import Type, Optional, List, Dict, Any

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client


class GetTickerCikMapInput(BaseModel):
    """Input schema for get_ticker_cik_map tool."""
    pass


class GetTickerCikMapTool(BaseTool):
    """
    Get the complete ticker-to-CIK mapping from SEC.
    
    Returns a list of all companies with their ticker, CIK, name, and exchange.
    This is useful for looking up company information or converting tickers to CIKs.
    """
    name: str = "get_ticker_cik_map"
    description: str = """
    Retrieves the complete mapping of stock tickers to CIK numbers from the SEC.
    Returns a list of all companies with their ticker symbol, CIK (10-digit padded),
    company name, and exchange. Use this to find company information or convert
    tickers to CIKs for other SEC tools.
    """
    args_schema: Type[BaseModel] = GetTickerCikMapInput

    def _run(self) -> str:
        client = get_default_client()
        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        
        try:
            response = client.get(url)
            data = response.json()
            
            # Normalize the response format
            result = {
                "data": data,
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to fetch ticker map: {str(e)}"]
            })


class TickerToCikInput(BaseModel):
    """Input schema for ticker_to_cik tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")


class TickerToCikTool(BaseTool):
    """
    Convert a stock ticker symbol to a CIK number.
    
    Takes a ticker symbol (e.g., 'AAPL') and returns the corresponding
    10-digit zero-padded CIK number (e.g., '0000320193').
    """
    name: str = "ticker_to_cik"
    description: str = """
    Converts a stock ticker symbol to its corresponding CIK (Central Index Key) number.
    CIK is a 10-digit zero-padded identifier used by the SEC. Example: 'AAPL' -> '0000320193'.
    Use this before calling other SEC tools that require a CIK.
    """
    args_schema: Type[BaseModel] = TickerToCikInput

    def _run(self, ticker: str) -> str:
        ticker_upper = ticker.upper().strip()
        client = get_default_client()
        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        
        try:
            response = client.get(url)
            ticker_map = response.json()
            
            # Find matching ticker
            cik = None
            company_name = None
            
            # SEC API returns: {"fields": ["cik", "name", "ticker", "exchange"], "data": [[cik, name, ticker, exchange], ...]}
            if isinstance(ticker_map, dict) and "fields" in ticker_map and "data" in ticker_map:
                fields = ticker_map["fields"]
                data_rows = ticker_map["data"]
                
                # Find indices for fields
                try:
                    cik_idx = fields.index("cik")
                    name_idx = fields.index("name")
                    ticker_idx = fields.index("ticker")
                except ValueError:
                    # Fallback if field names don't match expected
                    cik_idx, name_idx, ticker_idx = 0, 1, 2
                
                # Search through data rows
                for row in data_rows:
                    if len(row) > ticker_idx and str(row[ticker_idx]).upper() == ticker_upper:
                        cik = str(row[cik_idx])
                        company_name = row[name_idx] if len(row) > name_idx else None
                        break
            # Legacy format handling (if API changes back)
            elif isinstance(ticker_map, dict):
                for entry in ticker_map.values():
                    if isinstance(entry, dict) and entry.get('ticker', '').upper() == ticker_upper:
                        cik = str(entry.get('cik_str', entry.get('cik', '')))
                        company_name = entry.get('title', entry.get('name', ''))
                        break
            elif isinstance(ticker_map, list):
                for entry in ticker_map:
                    if isinstance(entry, dict) and entry.get('ticker', '').upper() == ticker_upper:
                        cik = str(entry.get('cik_str', entry.get('cik', '')))
                        company_name = entry.get('title', entry.get('name', ''))
                        break
            
            if cik:
                # Pad CIK to 10 digits
                cik_padded = cik.zfill(10)
                result = {
                    "data": {
                        "ticker": ticker_upper,
                        "cik": cik_padded,
                        "company_name": company_name
                    },
                    "source_urls": [url],
                    "warnings": []
                }
            else:
                result = {
                    "data": None,
                    "source_urls": [url],
                    "warnings": [f"Ticker '{ticker}' not found in SEC database"]
                }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to convert ticker to CIK: {str(e)}"]
            })


class GetCompanySubmissionsInput(BaseModel):
    """Input schema for get_company_submissions tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number (e.g., '0000320193')")


class GetCompanySubmissionsTool(BaseTool):
    """
    Get company submissions history from SEC.
    
    Retrieves the complete submissions JSON for a company, which includes:
    - Company metadata (name, SIC, addresses, etc.)
    - Recent filings (up to ~1000 most recent)
    - References to additional filing data if available
    
    This is the primary source for company filing information.
    """
    name: str = "get_company_submissions"
    description: str = """
    Retrieves the complete submissions history for a company by CIK.
    Returns company metadata and recent filings data. This is the primary
    source for discovering what filings a company has submitted to the SEC.
    Includes company name, SIC codes, addresses, and arrays of recent filings.
    """
    args_schema: Type[BaseModel] = GetCompanySubmissionsInput

    def _run(self, cik: str) -> str:
        # Ensure CIK is 10 digits, zero-padded
        cik_padded = cik.strip().zfill(10)
        client = get_default_client()
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        try:
            response = client.get(url)
            data = response.json()
            
            result = {
                "data": data,
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to fetch company submissions: {str(e)}"]
            })


class GetCompanyProfileInput(BaseModel):
    """Input schema for get_company_profile tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")


class GetCompanyProfileTool(BaseTool):
    """
    Get normalized company profile from ticker.
    
    Retrieves and normalizes company information including:
    - Entity name and former names
    - Ticker symbols and exchanges
    - SIC codes and industry classification
    - Business addresses
    - Filer flags and status
    
    This is a convenience tool that combines ticker lookup and submissions data.
    """
    name: str = "get_company_profile"
    description: str = """
    Retrieves a normalized company profile from a ticker symbol.
    Returns company name, former names, tickers, exchanges, SIC codes,
    addresses, and filer status. This combines ticker-to-CIK conversion
    with company submissions data to provide a complete company profile.
    """
    args_schema: Type[BaseModel] = GetCompanyProfileInput

    def _run(self, ticker: str) -> str:
        ticker_upper = ticker.upper().strip()
        client = get_default_client()
        
        # First, get CIK from ticker
        ticker_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        submissions_url = None
        warnings = []
        
        try:
            # Get ticker map
            response = client.get(ticker_url)
            ticker_map = response.json()
            
            # Find CIK
            cik = None
            company_name = None
            
            # SEC API returns: {"fields": ["cik", "name", "ticker", "exchange"], "data": [[cik, name, ticker, exchange], ...]}
            if isinstance(ticker_map, dict) and "fields" in ticker_map and "data" in ticker_map:
                fields = ticker_map["fields"]
                data_rows = ticker_map["data"]
                
                # Find indices for fields
                try:
                    cik_idx = fields.index("cik")
                    name_idx = fields.index("name")
                    ticker_idx = fields.index("ticker")
                except ValueError:
                    # Fallback if field names don't match expected
                    cik_idx, name_idx, ticker_idx = 0, 1, 2
                
                # Search through data rows
                for row in data_rows:
                    if len(row) > ticker_idx and str(row[ticker_idx]).upper() == ticker_upper:
                        cik = str(row[cik_idx])
                        company_name = row[name_idx] if len(row) > name_idx else None
                        break
            # Legacy format handling (if API changes back)
            elif isinstance(ticker_map, dict):
                for entry in ticker_map.values():
                    if isinstance(entry, dict) and entry.get('ticker', '').upper() == ticker_upper:
                        cik = str(entry.get('cik_str', entry.get('cik', '')))
                        company_name = entry.get('title', entry.get('name', ''))
                        break
            elif isinstance(ticker_map, list):
                for entry in ticker_map:
                    if isinstance(entry, dict) and entry.get('ticker', '').upper() == ticker_upper:
                        cik = str(entry.get('cik_str', entry.get('cik', '')))
                        company_name = entry.get('title', entry.get('name', ''))
                        break
            
            if not cik:
                return json.dumps({
                    "data": None,
                    "source_urls": [ticker_url],
                    "warnings": [f"Ticker '{ticker}' not found in SEC database"]
                })
            
            cik_padded = cik.zfill(10)
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
            
            # Get submissions
            response = client.get(submissions_url)
            submissions = response.json()
            
            # Normalize profile data
            profile = {
                "ticker": ticker_upper,
                "cik": cik_padded,
                "entity_name": submissions.get('name', company_name),
                "former_names": submissions.get('formerNames', []),
                "tickers": submissions.get('tickers', [ticker_upper]),
                "exchanges": submissions.get('exchanges', []),
                "sic": submissions.get('sic', ''),
                "sic_description": submissions.get('sicDescription', ''),
                "addresses": submissions.get('addresses', {}),
                "filer_flags": {
                    "well_known_seasoned_issuer": submissions.get('wksi', False),
                    "former_conformed_name": submissions.get('formerConformedName', ''),
                    "filer_category": submissions.get('category', ''),
                    "filer_type": submissions.get('filerType', '')
                }
            }
            
            result = {
                "data": profile,
                "source_urls": [ticker_url, submissions_url],
                "warnings": warnings
            }
            
            return json.dumps(result)
        except Exception as e:
            source_urls = [ticker_url]
            if submissions_url:
                source_urls.append(submissions_url)
            
            return json.dumps({
                "data": None,
                "source_urls": source_urls,
                "warnings": [f"Failed to fetch company profile: {str(e)}"]
            })
