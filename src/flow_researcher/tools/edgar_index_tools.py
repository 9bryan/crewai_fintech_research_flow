"""
EDGAR Index Files Tools.

These tools work with EDGAR daily and quarterly index files for discovering
filings by date and building custom searches.
"""

import json
import re
from typing import Type, Optional, List
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client


class ListDailyIndexPathsInput(BaseModel):
    """Input schema for list_daily_index_paths tool."""
    year: int = Field(..., description="Year (e.g., 2024)")
    quarter: Optional[int] = Field(
        default=None,
        ge=1,
        le=4,
        description="Quarter (1-4), optional"
    )


class ListDailyIndexPathsTool(BaseTool):
    """
    List daily index file paths.
    
    Enumerates likely index file paths (.idx, .gz, .zip) for a given year
    and optionally quarter under the daily-index directory.
    """
    name: str = "list_daily_index_paths"
    description: str = """
    Lists likely daily index file paths for a given year and optionally quarter.
    Returns paths to .idx, .gz, and .zip files that can be downloaded from
    the SEC's daily index directory.
    """
    args_schema: Type[BaseModel] = ListDailyIndexPathsInput

    def _run(self, year: int, quarter: Optional[int] = None) -> str:
        base_url = "https://www.sec.gov/Archives/edgar/daily-index"
        
        paths = []
        
        if quarter:
            # Quarterly paths
            for month in range((quarter - 1) * 3 + 1, quarter * 3 + 1):
                month_str = f"{month:02d}"
                paths.extend([
                    f"{base_url}/{year}/QTR{quarter}/master.{month_str}.idx",
                    f"{base_url}/{year}/QTR{quarter}/master.{month_str}.idx.gz",
                ])
        else:
            # All quarters
            for q in range(1, 5):
                for month in range((q - 1) * 3 + 1, q * 3 + 1):
                    month_str = f"{month:02d}"
                    paths.extend([
                        f"{base_url}/{year}/QTR{q}/master.{month_str}.idx",
                        f"{base_url}/{year}/QTR{q}/master.{month_str}.idx.gz",
                    ])
        
        result = {
            "data": {
                "year": year,
                "quarter": quarter,
                "paths": paths,
                "count": len(paths)
            },
            "source_urls": [base_url],
            "warnings": []
        }
        
        return json.dumps(result)


class DownloadDailyMasterIndexInput(BaseModel):
    """Input schema for download_daily_master_index tool."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    dest_path: str = Field(..., description="Local path where to save the index file")


class DownloadDailyMasterIndexTool(BaseTool):
    """
    Download daily master index file.
    
    Downloads the master index file for a specific date. Tries .idx, .gz,
    and .zip variants.
    """
    name: str = "download_daily_master_index"
    description: str = """
    Downloads the daily master index file for a specific date. Attempts to
    download .idx, .idx.gz, or .zip variants. The master index contains
    all filings for that day.
    """
    args_schema: Type[BaseModel] = DownloadDailyMasterIndexInput

    def _run(self, date: str, dest_path: str) -> str:
        try:
            # Parse date
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month
            quarter = (month - 1) // 3 + 1
            
            base_url = "https://www.sec.gov/Archives/edgar/daily-index"
            month_str = f"{month:02d}"
            
            # Try different file formats
            urls_to_try = [
                f"{base_url}/{year}/QTR{quarter}/master.{month_str}.idx",
                f"{base_url}/{year}/QTR{quarter}/master.{month_str}.idx.gz",
            ]
            
            client = get_default_client()
            downloaded_path = None
            source_url = None
            
            for url in urls_to_try:
                try:
                    downloaded_path = client.download(url, dest_path)
                    source_url = url
                    break
                except:
                    continue
            
            if downloaded_path:
                result = {
                    "data": {
                        "downloaded_path": downloaded_path,
                        "url": source_url,
                        "date": date
                    },
                    "source_urls": [source_url],
                    "warnings": []
                }
            else:
                result = {
                    "data": None,
                    "source_urls": urls_to_try,
                    "warnings": [f"Failed to download master index for {date} from any URL"]
                }
            
            return json.dumps(result)
        except ValueError:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": ["Invalid date format. Use YYYY-MM-DD format."]
            })
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to download daily master index: {str(e)}"]
            })


class ParseMasterIdxInput(BaseModel):
    """Input schema for parse_master_idx tool."""
    file_path: str = Field(..., description="Path to the master.idx file")


class ParseMasterIdxTool(BaseTool):
    """
    Parse master index file.
    
    Parses a master index file and returns rows with CIK, company name,
    form type, date filed, and EDGAR path.
    """
    name: str = "parse_master_idx"
    description: str = """
    Parses a master index file and extracts filing information. Returns rows
    with: cik, company_name, form_type, date_filed, edgar_path. The master
    index file format is a fixed-width text file with header information.
    """
    args_schema: Type[BaseModel] = ParseMasterIdxInput

    def _run(self, file_path: str) -> str:
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return json.dumps({
                    "data": [],
                    "source_urls": [],
                    "warnings": [f"File not found: {file_path}"]
                })
            
            rows = []
            with open(file_path_obj, 'r', encoding='latin-1') as f:
                lines = f.readlines()
            
            # Master index format: skip header lines (usually first few lines)
            # Then parse fixed-width format
            # Format: CIK|Company Name|Form Type|Date Filed|File Name
            data_started = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip header lines
                if not data_started:
                    if '|' in line and 'CIK' in line.upper():
                        data_started = True
                        continue
                    continue
                
                # Parse line (pipe-separated or fixed-width)
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        try:
                            cik = parts[0].strip()
                            company_name = parts[1].strip()
                            form_type = parts[2].strip()
                            date_filed = parts[3].strip()
                            edgar_path = parts[4].strip() if len(parts) > 4 else ""
                            
                            rows.append({
                                "cik": cik,
                                "company_name": company_name,
                                "form_type": form_type,
                                "date_filed": date_filed,
                                "edgar_path": edgar_path
                            })
                        except (IndexError, ValueError):
                            continue
            
            result = {
                "data": {
                    "rows": rows,
                    "count": len(rows)
                },
                "source_urls": [],
                "warnings": [] if rows else ["No rows parsed from master index file"]
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": [],
                "source_urls": [],
                "warnings": [f"Failed to parse master index: {str(e)}"]
            })


class FindFilingsInMasterIdxInput(BaseModel):
    """Input schema for find_filings_in_master_idx tool."""
    rows: str = Field(
        ...,
        description="JSON string of rows from parse_master_idx tool"
    )
    cik: Optional[str] = Field(default=None, description="Filter by CIK")
    forms: Optional[List[str]] = Field(
        default=None,
        description="Filter by form types (e.g., ['10-Q', '10-K'])"
    )


class FindFilingsInMasterIdxTool(BaseTool):
    """
    Find filings in master index rows.
    
    Filters master index rows by CIK and/or form types.
    """
    name: str = "find_filings_in_master_idx"
    description: str = """
    Filters master index rows by CIK and/or form types. Useful for finding
    specific filings for a company or specific form types across companies.
    """
    args_schema: Type[BaseModel] = FindFilingsInMasterIdxInput

    def _run(self, rows: str, cik: Optional[str] = None, forms: Optional[List[str]] = None) -> str:
        try:
            if isinstance(rows, str):
                data = json.loads(rows)
            else:
                data = rows
            
            # Extract rows from data structure
            if isinstance(data, dict) and "data" in data:
                rows_list = data["data"].get("rows", [])
            elif isinstance(data, dict) and "rows" in data:
                rows_list = data["rows"]
            elif isinstance(data, list):
                rows_list = data
            else:
                rows_list = []
            
            # Apply filters
            filtered = rows_list
            if cik:
                cik_padded = cik.strip().zfill(10)
                filtered = [r for r in filtered if r.get("cik", "").zfill(10) == cik_padded]
            if forms:
                forms_upper = [f.upper() for f in forms]
                filtered = [r for r in filtered if r.get("form_type", "").upper() in forms_upper]
            
            result = {
                "data": {
                    "rows": filtered,
                    "count": len(filtered),
                    "original_count": len(rows_list),
                    "filters_applied": {
                        "cik": cik,
                        "forms": forms
                    }
                },
                "source_urls": [],
                "warnings": []
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": {"rows": [], "count": 0, "original_count": 0},
                "source_urls": [],
                "warnings": ["Invalid JSON in rows parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": {"rows": [], "count": 0, "original_count": 0},
                "source_urls": [],
                "warnings": [f"Failed to find filings: {str(e)}"]
            })


class EdgarPathToDocUrlInput(BaseModel):
    """Input schema for edgar_path_to_doc_url tool."""
    edgar_path: str = Field(
        ...,
        description="EDGAR path from index (e.g., 'edgar/data/320193/000032019325000010/...')"
    )


class EdgarPathToDocUrlTool(BaseTool):
    """
    Convert EDGAR path to document URL.
    
    Converts an EDGAR path from index files into a full URL.
    """
    name: str = "edgar_path_to_doc_url"
    description: str = """
    Converts an EDGAR path from index files (e.g., 'edgar/data/...') into a
    full URL (https://www.sec.gov/Archives/...). This is needed to access
    documents referenced in index files.
    """
    args_schema: Type[BaseModel] = EdgarPathToDocUrlInput

    def _run(self, edgar_path: str) -> str:
        # Remove leading 'edgar/' or 'edgar/data/' if present
        path = edgar_path.lstrip('/')
        if path.startswith('edgar/data/'):
            path = path[11:]  # Remove 'edgar/data/'
        elif path.startswith('edgar/'):
            path = path[6:]  # Remove 'edgar/'
        
        url = f"https://www.sec.gov/Archives/edgar/data/{path}"
        
        result = {
            "data": {
                "url": url,
                "edgar_path": edgar_path
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)
