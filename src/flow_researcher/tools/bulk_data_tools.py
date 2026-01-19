"""
Bulk Data Tools.

These tools download and extract SEC bulk data ZIP files for offline
or fast lookup of submissions and XBRL facts.
"""

import json
import zipfile
from typing import Type
from pathlib import Path

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client


class DownloadBulkSubmissionsZipInput(BaseModel):
    """Input schema for download_bulk_submissions_zip tool."""
    dest_path: str = Field(..., description="Local path where to save the ZIP file")


class DownloadBulkSubmissionsZipTool(BaseTool):
    """
    Download bulk submissions ZIP file.
    
    Downloads the nightly bulk submissions ZIP file containing all company
    submissions data.
    """
    name: str = "download_bulk_submissions_zip"
    description: str = """
    Downloads the bulk submissions ZIP file from SEC. This file contains
    all company submissions data and is updated nightly. Useful for offline
    or fast lookup without making individual API calls.
    """
    args_schema: Type[BaseModel] = DownloadBulkSubmissionsZipInput

    def _run(self, dest_path: str) -> str:
        client = get_default_client()
        url = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
        
        try:
            downloaded_path = client.download(url, dest_path)
            
            result = {
                "data": {
                    "downloaded_path": downloaded_path,
                    "url": url,
                    "file_size": Path(downloaded_path).stat().st_size if Path(downloaded_path).exists() else None
                },
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to download bulk submissions ZIP: {str(e)}"]
            })


class DownloadBulkCompanyfactsZipInput(BaseModel):
    """Input schema for download_bulk_companyfacts_zip tool."""
    dest_path: str = Field(..., description="Local path where to save the ZIP file")


class DownloadBulkCompanyfactsZipTool(BaseTool):
    """
    Download bulk company facts ZIP file.
    
    Downloads the nightly bulk company facts ZIP file containing all XBRL
    company facts data.
    """
    name: str = "download_bulk_companyfacts_zip"
    description: str = """
    Downloads the bulk company facts ZIP file from SEC. This file contains
    all XBRL company facts data and is updated nightly. Useful for offline
    or fast lookup of financial data without making individual API calls.
    """
    args_schema: Type[BaseModel] = DownloadBulkCompanyfactsZipInput

    def _run(self, dest_path: str) -> str:
        client = get_default_client()
        url = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
        
        try:
            downloaded_path = client.download(url, dest_path)
            
            result = {
                "data": {
                    "downloaded_path": downloaded_path,
                    "url": url,
                    "file_size": Path(downloaded_path).stat().st_size if Path(downloaded_path).exists() else None
                },
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to download bulk company facts ZIP: {str(e)}"]
            })


class ExtractBulkZipInput(BaseModel):
    """Input schema for extract_bulk_zip tool."""
    zip_path: str = Field(..., description="Path to the ZIP file to extract")
    dest_dir: str = Field(..., description="Directory where to extract files")


class ExtractBulkZipTool(BaseTool):
    """
    Extract bulk ZIP file.
    
    Extracts a bulk ZIP file (submissions or company facts) into JSON files
    in the specified directory.
    """
    name: str = "extract_bulk_zip"
    description: str = """
    Extracts a bulk ZIP file (submissions or company facts) into individual
    JSON files in the specified directory. Each company's data is typically
    in a separate JSON file.
    """
    args_schema: Type[BaseModel] = ExtractBulkZipInput

    def _run(self, zip_path: str, dest_dir: str) -> str:
        try:
            zip_path_obj = Path(zip_path)
            dest_dir_obj = Path(dest_dir)
            
            if not zip_path_obj.exists():
                return json.dumps({
                    "data": None,
                    "source_urls": [],
                    "warnings": [f"ZIP file not found: {zip_path}"]
                })
            
            # Create destination directory
            dest_dir_obj.mkdir(parents=True, exist_ok=True)
            
            extracted_files = []
            with zipfile.ZipFile(zip_path_obj, 'r') as zip_ref:
                zip_ref.extractall(dest_dir_obj)
                extracted_files = zip_ref.namelist()
            
            result = {
                "data": {
                    "dest_dir": str(dest_dir_obj.absolute()),
                    "extracted_files": extracted_files,
                    "file_count": len(extracted_files)
                },
                "source_urls": [],
                "warnings": []
            }
            
            return json.dumps(result)
        except zipfile.BadZipFile:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Invalid ZIP file: {zip_path}"]
            })
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [],
                "warnings": [f"Failed to extract ZIP file: {str(e)}"]
            })
