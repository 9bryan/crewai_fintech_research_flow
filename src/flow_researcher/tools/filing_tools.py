"""
Filings Discovery & Metadata Tools for SEC data.

These tools help discover and retrieve metadata about SEC filings
including recent filings, latest filings by form type, date ranges, etc.
"""

import json
from typing import Type, Optional, List, Dict, Any
from datetime import datetime, date

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client
from .company_tools import TickerToCikTool


class ListRecentFilingsInput(BaseModel):
    """Input schema for list_recent_filings tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number (e.g., '0000320193')")
    forms: Optional[List[str]] = Field(
        default=None,
        description="Optional list of form types to filter (e.g., ['10-Q', '10-K', '8-K'])"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of filings to return (1-1000)"
    )


class ListRecentFilingsTool(BaseTool):
    """
    List recent filings for a company.
    
    Retrieves a list of recent filings for a company, optionally filtered
    by form type. Returns normalized filing metadata including form type,
    filing date, report date, accession number, and primary document.
    """
    name: str = "list_recent_filings"
    description: str = """
    Lists recent SEC filings for a company by CIK. Can optionally filter
    by form types (e.g., ['10-Q', '10-K', '8-K']). Returns filing metadata
    including form type, filing date, report date, accession number, and
    primary document. The submissions API provides up to ~1000 most recent filings.
    """
    args_schema: Type[BaseModel] = ListRecentFilingsInput

    def _run(self, cik: str, forms: Optional[List[str]] = None, limit: int = 100) -> str:
        cik_padded = cik.strip().zfill(10)
        client = get_default_client()
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        try:
            response = client.get(url)
            submissions = response.json()
            
            # Get filings array
            filings = submissions.get('filings', {}).get('recent', {})
            
            if not filings or 'accessionNumber' not in filings:
                return json.dumps({
                    "data": [],
                    "source_urls": [url],
                    "warnings": ["No filings found in submissions data"]
                })
            
            # Normalize filings
            normalized = []
            accession_numbers = filings.get('accessionNumber', [])
            form_types = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            report_dates = filings.get('reportDate', [])
            acceptance_dates = filings.get('acceptanceDateTime', [])
            primary_docs = filings.get('primaryDocument', [])
            
            for i in range(len(accession_numbers)):
                form = form_types[i] if i < len(form_types) else None
                
                # Filter by forms if specified
                if forms and form not in forms:
                    continue
                
                filing_meta = {
                    "form": form,
                    "filingDate": filing_dates[i] if i < len(filing_dates) else None,
                    "reportDate": report_dates[i] if i < len(report_dates) else None,
                    "acceptanceDateTime": acceptance_dates[i] if i < len(acceptance_dates) else None,
                    "accessionNumber": accession_numbers[i],
                    "primaryDocument": primary_docs[i] if i < len(primary_docs) else None
                }
                
                normalized.append(filing_meta)
                
                if len(normalized) >= limit:
                    break
            
            result = {
                "data": normalized,
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": [],
                "source_urls": [url],
                "warnings": [f"Failed to list filings: {str(e)}"]
            })


class GetLatestFilingInput(BaseModel):
    """Input schema for get_latest_filing tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number (e.g., '0000320193')")
    form: str = Field(..., description="Form type (e.g., '10-Q', '10-K', '8-K')")


class GetLatestFilingTool(BaseTool):
    """
    Get the most recent filing of a specific form type.
    
    Returns the single most recent filing matching the specified form type
    (e.g., '10-Q', '10-K', '8-K'). Useful for getting the latest quarterly
    or annual report.
    """
    name: str = "get_latest_filing"
    description: str = """
    Gets the most recent filing of a specific form type for a company.
    Returns the latest filing matching the form type (e.g., '10-Q' for quarterly
    reports, '10-K' for annual reports, '8-K' for current reports).
    """
    args_schema: Type[BaseModel] = GetLatestFilingInput

    def _run(self, cik: str, form: str) -> str:
        cik_padded = cik.strip().zfill(10)
        form_upper = form.upper().strip()
        client = get_default_client()
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        try:
            response = client.get(url)
            submissions = response.json()
            
            filings = submissions.get('filings', {}).get('recent', {})
            
            if not filings or 'accessionNumber' not in filings:
                return json.dumps({
                    "data": None,
                    "source_urls": [url],
                    "warnings": ["No filings found in submissions data"]
                })
            
            # Find latest matching form
            accession_numbers = filings.get('accessionNumber', [])
            form_types = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            report_dates = filings.get('reportDate', [])
            acceptance_dates = filings.get('acceptanceDateTime', [])
            primary_docs = filings.get('primaryDocument', [])
            
            latest_filing = None
            latest_date = None
            
            for i in range(len(accession_numbers)):
                if i < len(form_types) and form_types[i] == form_upper:
                    filing_date = filing_dates[i] if i < len(filing_dates) else None
                    
                    if filing_date:
                        # Compare dates to find latest
                        if latest_date is None or filing_date > latest_date:
                            latest_date = filing_date
                            latest_filing = {
                                "form": form_upper,
                                "filingDate": filing_date,
                                "reportDate": report_dates[i] if i < len(report_dates) else None,
                                "acceptanceDateTime": acceptance_dates[i] if i < len(acceptance_dates) else None,
                                "accessionNumber": accession_numbers[i],
                                "primaryDocument": primary_docs[i] if i < len(primary_docs) else None
                            }
            
            if latest_filing:
                result = {
                    "data": latest_filing,
                    "source_urls": [url],
                    "warnings": []
                }
            else:
                result = {
                    "data": None,
                    "source_urls": [url],
                    "warnings": [f"No {form_upper} filings found for this company"]
                }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to get latest filing: {str(e)}"]
            })


class GetFilingsByDateRangeInput(BaseModel):
    """Input schema for get_filings_by_date_range tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number (e.g., '0000320193')")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    forms: Optional[List[str]] = Field(
        default=None,
        description="Optional list of form types to filter (e.g., ['10-Q', '10-K'])"
    )


class GetFilingsByDateRangeTool(BaseTool):
    """
    Get filings within a date range.
    
    Retrieves all filings filed within the specified date range, optionally
    filtered by form types. Uses submissions data and may reference additional
    filing JSON files for older ranges if available.
    """
    name: str = "get_filings_by_date_range"
    description: str = """
    Gets all SEC filings for a company within a specified date range.
    Optionally filters by form types. Date format: YYYY-MM-DD.
    Returns filings that were filed (filingDate) within the range.
    """
    args_schema: Type[BaseModel] = GetFilingsByDateRangeInput

    def _run(self, cik: str, start_date: str, end_date: str, forms: Optional[List[str]] = None) -> str:
        cik_padded = cik.strip().zfill(10)
        client = get_default_client()
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        try:
            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start > end:
                return json.dumps({
                    "data": [],
                    "source_urls": [url],
                    "warnings": ["Start date must be before or equal to end date"]
                })
            
            response = client.get(url)
            submissions = response.json()
            
            filings = submissions.get('filings', {}).get('recent', {})
            
            if not filings or 'accessionNumber' not in filings:
                return json.dumps({
                    "data": [],
                    "source_urls": [url],
                    "warnings": ["No filings found in submissions data"]
                })
            
            # Filter filings by date range
            normalized = []
            accession_numbers = filings.get('accessionNumber', [])
            form_types = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            report_dates = filings.get('reportDate', [])
            acceptance_dates = filings.get('acceptanceDateTime', [])
            primary_docs = filings.get('primaryDocument', [])
            
            for i in range(len(accession_numbers)):
                form = form_types[i] if i < len(form_types) else None
                filing_date_str = filing_dates[i] if i < len(filing_dates) else None
                
                # Filter by forms if specified
                if forms and form not in forms:
                    continue
                
                # Filter by date range
                if filing_date_str:
                    try:
                        filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").date()
                        if start <= filing_date <= end:
                            filing_meta = {
                                "form": form,
                                "filingDate": filing_date_str,
                                "reportDate": report_dates[i] if i < len(report_dates) else None,
                                "acceptanceDateTime": acceptance_dates[i] if i < len(acceptance_dates) else None,
                                "accessionNumber": accession_numbers[i],
                                "primaryDocument": primary_docs[i] if i < len(primary_docs) else None
                            }
                            normalized.append(filing_meta)
                    except ValueError:
                        # Skip if date parsing fails
                        continue
            
            result = {
                "data": normalized,
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except ValueError as e:
            return json.dumps({
                "data": [],
                "source_urls": [url],
                "warnings": [f"Invalid date format: {str(e)}. Use YYYY-MM-DD format."]
            })
        except Exception as e:
            return json.dumps({
                "data": [],
                "source_urls": [url],
                "warnings": [f"Failed to get filings by date range: {str(e)}"]
            })


class GetFilingAcceptanceDatetimeInput(BaseModel):
    """Input schema for get_filing_acceptance_datetime tool."""
    filing_meta: str = Field(
        ...,
        description="JSON string of filing metadata containing acceptanceDateTime field"
    )


class GetFilingAcceptanceDatetimeTool(BaseTool):
    """
    Extract acceptance datetime from filing metadata.
    
    Extracts the acceptance timestamp from filing metadata, which indicates
    when the SEC accepted the filing. Useful for precise timing information.
    """
    name: str = "get_filing_acceptance_datetime"
    description: str = """
    Extracts the acceptance datetime from filing metadata. Returns the ISO
    datetime string when the SEC accepted the filing, or a warning if unavailable.
    Useful for determining the exact time a filing was accepted by the SEC.
    """
    args_schema: Type[BaseModel] = GetFilingAcceptanceDatetimeInput

    def _run(self, filing_meta: str) -> str:
        try:
            # Parse filing metadata
            if isinstance(filing_meta, str):
                meta = json.loads(filing_meta)
            else:
                meta = filing_meta
            
            acceptance_dt = meta.get('acceptanceDateTime')
            
            if acceptance_dt:
                result = {
                    "data": {
                        "acceptanceDateTime": acceptance_dt,
                        "iso_format": acceptance_dt
                    },
                    "source_urls": [],
                    "warnings": []
                }
            else:
                result = {
                    "data": None,
                    "source_urls": [],
                    "warnings": ["Acceptance datetime not available in filing metadata"]
                }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": ["Invalid JSON in filing_meta parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to extract acceptance datetime: {str(e)}"]
            })
