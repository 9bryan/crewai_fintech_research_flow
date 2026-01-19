"""
Common Higher-Level Convenience Tools.

These tools combine multiple lower-level tools to provide convenient
high-level operations for common use cases.
"""

import json
from typing import Type, Optional, List

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .company_tools import TickerToCikTool, GetCompanySubmissionsTool
from .filing_tools import ListRecentFilingsTool, GetLatestFilingTool
from .xbrl_tools import GetCompanyFactsTool, GetCompanyConceptTool


class GetLatest10qOr10kInput(BaseModel):
    """Input schema for get_latest_10q_or_10k tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")


class GetLatest10qOr10kTool(BaseTool):
    """
    Get latest 10-Q or 10-K filing.
    
    Convenience tool that gets the most recent quarterly (10-Q) or annual (10-K)
    report for a company. Returns whichever is more recent.
    """
    name: str = "get_latest_10q_or_10k"
    description: str = """
    Gets the most recent 10-Q (quarterly) or 10-K (annual) filing for a company.
    Returns whichever filing is more recent. This is a common use case for
    financial analysis.
    """
    args_schema: Type[BaseModel] = GetLatest10qOr10kInput

    def _run(self, ticker: str) -> str:
        try:
            # Convert ticker to CIK
            ticker_tool = TickerToCikTool()
            cik_result = json.loads(ticker_tool._run(ticker))
            
            if not cik_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"],
                    "warnings": cik_result["warnings"]
                })
            
            cik = cik_result["data"]["cik"]
            
            # Get recent filings filtered for 10-Q and 10-K
            filings_tool = ListRecentFilingsTool()
            filings_result = json.loads(filings_tool._run(cik, forms=["10-Q", "10-K"], limit=1))
            
            if not filings_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"] + filings_result["source_urls"],
                    "warnings": ["No 10-Q or 10-K filings found"]
                })
            
            latest = filings_result["data"][0]
            
            result = {
                "data": latest,
                "source_urls": cik_result["source_urls"] + filings_result["source_urls"],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to get latest 10-Q or 10-K: {str(e)}"]
            })


class GetLatest8kInput(BaseModel):
    """Input schema for get_latest_8k tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")


class GetLatest8kTool(BaseTool):
    """
    Get latest 8-K filing.
    
    Convenience tool that gets the most recent 8-K (current report) filing
    for a company.
    """
    name: str = "get_latest_8k"
    description: str = """
    Gets the most recent 8-K (current report) filing for a company. 8-K filings
    are used to report material events that shareholders should know about.
    """
    args_schema: Type[BaseModel] = GetLatest8kInput

    def _run(self, ticker: str) -> str:
        try:
            # Convert ticker to CIK
            ticker_tool = TickerToCikTool()
            cik_result = json.loads(ticker_tool._run(ticker))
            
            if not cik_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"],
                    "warnings": cik_result["warnings"]
                })
            
            cik = cik_result["data"]["cik"]
            
            # Get latest 8-K
            latest_tool = GetLatestFilingTool()
            latest_result = json.loads(latest_tool._run(cik, "8-K"))
            
            result = {
                "data": latest_result["data"],
                "source_urls": cik_result["source_urls"] + latest_result["source_urls"],
                "warnings": latest_result["warnings"]
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to get latest 8-K: {str(e)}"]
            })


class GetFilingDocsBundleInput(BaseModel):
    """Input schema for get_filing_docs_bundle tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")
    form: str = Field(..., description="Form type (e.g., '10-Q', '10-K', '8-K')")


class GetFilingDocsBundleTool(BaseTool):
    """
    Get filing documents bundle.
    
    Convenience tool that gets a filing and all its associated documents,
    including the filing metadata, document index, and URLs for primary
    documents and exhibits.
    """
    name: str = "get_filing_docs_bundle"
    description: str = """
    Gets a complete filing documents bundle including: filing metadata, parsed
    document index list, URLs for primary documents and exhibits, and optional
    downloaded local paths. This provides everything needed to work with a filing.
    """
    args_schema: Type[BaseModel] = GetFilingDocsBundleInput

    def _run(self, ticker: str, form: str) -> str:
        try:
            from .company_tools import TickerToCikTool
            from .filing_tools import GetLatestFilingTool
            from .edgar_url_tools import BuildFilingIndexUrlTool
            from .filing_document_tools import GetFilingIndexHtmlTool, ParseFilingIndexDocumentsTool
            
            # Convert ticker to CIK
            ticker_tool = TickerToCikTool()
            cik_result = json.loads(ticker_tool._run(ticker))
            
            if not cik_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"],
                    "warnings": cik_result["warnings"]
                })
            
            cik = cik_result["data"]["cik"]
            
            # Get latest filing
            latest_tool = GetLatestFilingTool()
            latest_result = json.loads(latest_tool._run(cik, form))
            
            if not latest_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"] + latest_result["source_urls"],
                    "warnings": latest_result["warnings"]
                })
            
            filing_meta = latest_result["data"]
            accession = filing_meta["accessionNumber"]
            
            # Get filing index HTML
            index_tool = GetFilingIndexHtmlTool()
            index_result = json.loads(index_tool._run(cik, accession))
            
            documents = []
            if index_result["data"]:
                # Parse documents
                parse_tool = ParseFilingIndexDocumentsTool()
                parse_result = json.loads(parse_tool._run(index_result["data"]["html"]))
                documents = parse_result["data"]
            
            result = {
                "data": {
                    "filing_meta": filing_meta,
                    "documents": documents,
                    "document_count": len(documents),
                    "index_url": index_result["data"]["url"] if index_result["data"] else None
                },
                "source_urls": (
                    cik_result["source_urls"] +
                    latest_result["source_urls"] +
                    index_result["source_urls"]
                ),
                "warnings": latest_result["warnings"] + index_result["warnings"]
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to get filing docs bundle: {str(e)}"]
            })


class GetKeyFinancialSeriesInput(BaseModel):
    """Input schema for get_key_financial_series tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")
    tags: List[str] = Field(
        ...,
        description="List of XBRL tags to retrieve (e.g., ['Revenues', 'NetIncomeLoss', 'Assets'])"
    )


class GetKeyFinancialSeriesTool(BaseTool):
    """
    Get key financial series.
    
    Convenience tool that retrieves time-series data for multiple XBRL tags
    and returns normalized series aligned by period.
    """
    name: str = "get_key_financial_series"
    description: str = """
    Retrieves time-series financial data for multiple XBRL tags and returns
    normalized series aligned by period. Useful for getting key financial
    metrics like Revenues, Net Income, Assets, etc. over time.
    """
    args_schema: Type[BaseModel] = GetKeyFinancialSeriesInput

    def _run(self, ticker: str, tags: List[str]) -> str:
        try:
            # Convert ticker to CIK
            ticker_tool = TickerToCikTool()
            cik_result = json.loads(ticker_tool._run(ticker))
            
            if not cik_result["data"]:
                return json.dumps({
                    "data": None,
                    "source_urls": cik_result["source_urls"],
                    "warnings": cik_result["warnings"]
                })
            
            cik = cik_result["data"]["cik"]
            
            # Get concepts for each tag
            concept_tool = GetCompanyConceptTool()
            series_data = {}
            source_urls = cik_result["source_urls"]
            warnings = []
            
            for tag in tags:
                try:
                    concept_result = json.loads(concept_tool._run(cik, "us-gaap", tag))
                    source_urls.extend(concept_result.get("source_urls", []))
                    
                    if concept_result["data"]:
                        # Extract units and facts
                        units_data = concept_result["data"].get("units", {})
                        series_data[tag] = {
                            "units": list(units_data.keys()),
                            "facts": units_data
                        }
                    else:
                        warnings.append(f"No data found for tag '{tag}'")
                except Exception as e:
                    warnings.append(f"Failed to get data for tag '{tag}': {str(e)}")
            
            result = {
                "data": {
                    "ticker": ticker,
                    "cik": cik,
                    "series": series_data,
                    "tags_requested": tags,
                    "tags_found": list(series_data.keys())
                },
                "source_urls": source_urls,
                "warnings": warnings
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to get key financial series: {str(e)}"]
            })
