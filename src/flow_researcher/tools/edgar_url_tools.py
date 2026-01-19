"""
EDGAR Archive URL Construction Tools.

These tools help construct URLs for accessing EDGAR filing documents
and archives.
"""

import json
from typing import Type

from pydantic import BaseModel, Field

from crewai.tools import BaseTool


class AccessionToNodashesInput(BaseModel):
    """Input schema for accession_to_nodashes tool."""
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class AccessionToNodashesTool(BaseTool):
    """
    Convert accession number from dashed format to no-dashes format.
    
    Converts an accession number like '0000320193-25-000010' to
    '000032019325000010' by removing dashes.
    """
    name: str = "accession_to_nodashes"
    description: str = """
    Converts an accession number from dashed format to no-dashes format.
    Example: '0000320193-25-000010' -> '000032019325000010'.
    This is needed for constructing some EDGAR URLs.
    """
    args_schema: Type[BaseModel] = AccessionToNodashesInput

    def _run(self, accession_with_dashes: str) -> str:
        accession_no_dashes = accession_with_dashes.replace("-", "")
        
        result = {
            "data": {
                "accession_with_dashes": accession_with_dashes,
                "accession_no_dashes": accession_no_dashes
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)


class BuildFilingIndexUrlInput(BaseModel):
    """Input schema for build_filing_index_url tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class BuildFilingIndexUrlTool(BaseTool):
    """
    Build URL for filing index HTML page.
    
    Constructs the URL to the filing index page which lists all documents
    in a filing submission.
    """
    name: str = "build_filing_index_url"
    description: str = """
    Builds the URL for a filing's index HTML page. The index page lists all
    documents in a filing submission. URL format:
    https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-WITH-DASHES}-index.html
    """
    args_schema: Type[BaseModel] = BuildFilingIndexUrlInput

    def _run(self, cik: str, accession_with_dashes: str) -> str:
        cik_padded = cik.strip().zfill(10)
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{accession_with_dashes}-index.html"
        
        result = {
            "data": {
                "url": url,
                "cik": cik_padded,
                "accession": accession_with_dashes
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)


class BuildCompleteSubmissionTxtUrlInput(BaseModel):
    """Input schema for build_complete_submission_txt_url tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class BuildCompleteSubmissionTxtUrlTool(BaseTool):
    """
    Build URL for complete submission text file.
    
    Constructs the URL to the complete submission text file (.txt) which
    contains the entire filing in text format.
    """
    name: str = "build_complete_submission_txt_url"
    description: str = """
    Builds the URL for a filing's complete submission text file. This is a
    single text file containing the entire filing. URL format:
    https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-WITH-DASHES}.txt
    """
    args_schema: Type[BaseModel] = BuildCompleteSubmissionTxtUrlInput

    def _run(self, cik: str, accession_with_dashes: str) -> str:
        cik_padded = cik.strip().zfill(10)
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{accession_with_dashes}.txt"
        
        result = {
            "data": {
                "url": url,
                "cik": cik_padded,
                "accession": accession_with_dashes
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)


class BuildFilingFolderUrlInput(BaseModel):
    """Input schema for build_filing_folder_url tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class BuildFilingFolderUrlTool(BaseTool):
    """
    Build URL for filing folder/directory.
    
    Constructs the base URL for a filing's folder which contains all
    documents for that filing.
    """
    name: str = "build_filing_folder_url"
    description: str = """
    Builds the base URL for a filing's folder/directory. This folder contains
    all documents for the filing. URL format:
    https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-NO-DASHES}/
    Note: Uses accession number WITHOUT dashes.
    """
    args_schema: Type[BaseModel] = BuildFilingFolderUrlInput

    def _run(self, cik: str, accession_with_dashes: str) -> str:
        cik_padded = cik.strip().zfill(10)
        accession_no_dashes = accession_with_dashes.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{accession_no_dashes}/"
        
        result = {
            "data": {
                "url": url,
                "cik": cik_padded,
                "accession_with_dashes": accession_with_dashes,
                "accession_no_dashes": accession_no_dashes
            },
            "source_urls": [],
            "warnings": []
        }
        
        return json.dumps(result)
