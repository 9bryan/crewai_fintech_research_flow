"""
Filing Document Index & Retrieval Tools.

These tools help retrieve and parse filing documents from EDGAR archives.
"""

import json
import re
from typing import Type, Optional, List, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client
from .edgar_url_tools import BuildFilingIndexUrlTool, BuildCompleteSubmissionTxtUrlTool


class GetFilingIndexHtmlInput(BaseModel):
    """Input schema for get_filing_index_html tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class GetFilingIndexHtmlTool(BaseTool):
    """
    Get filing index HTML page.
    
    Fetches the HTML index page for a filing which lists all documents
    in the submission.
    """
    name: str = "get_filing_index_html"
    description: str = """
    Fetches the HTML index page for a filing. This page lists all documents
    in the filing submission. Returns the raw HTML content.
    """
    args_schema: Type[BaseModel] = GetFilingIndexHtmlInput

    def _run(self, cik: str, accession_with_dashes: str) -> str:
        client = get_default_client()
        
        # Build URL
        url_tool = BuildFilingIndexUrlTool()
        url_result = json.loads(url_tool._run(cik, accession_with_dashes))
        url = url_result["data"]["url"]
        
        try:
            response = client.get(url)
            html_content = response.text
            
            result = {
                "data": {
                    "html": html_content,
                    "url": url
                },
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to fetch filing index HTML: {str(e)}"]
            })


class ParseFilingIndexDocumentsInput(BaseModel):
    """Input schema for parse_filing_index_documents tool."""
    index_html: str = Field(..., description="HTML content from filing index page")


class ParseFilingIndexDocumentsTool(BaseTool):
    """
    Parse filing index HTML into document list.
    
    Parses the filing index HTML page to extract a list of all documents
    in the filing, including their filenames, descriptions, types, and URLs.
    """
    name: str = "parse_filing_index_documents"
    description: str = """
    Parses the filing index HTML page to extract a list of all documents
    in the filing. Returns document metadata including filename, description,
    type (e.g., EX-99.1, 10-Q, XML), URL, and size.
    """
    args_schema: Type[BaseModel] = ParseFilingIndexDocumentsInput

    def _run(self, index_html: str) -> str:
        try:
            documents = []
            
            # EDGAR index pages have a table with document information
            # Pattern: Look for table rows with document links
            # The structure varies, but typically has links to documents
            
            # Try to find document links and extract information
            # Common pattern: <a href="...">filename</a> with description
            
            # Extract base URL from HTML if present
            base_url_match = re.search(r'<base\s+href="([^"]+)"', index_html, re.IGNORECASE)
            base_url = base_url_match.group(1) if base_url_match else ""
            
            # Find all document links - look for patterns like:
            # <a href="filename">Description</a>
            # or table rows with document information
            
            # Simple approach: find all links that look like document files
            doc_link_pattern = r'<a\s+href="([^"]+\.(?:txt|html|htm|xml|pdf))"[^>]*>([^<]+)</a>'
            matches = re.finditer(doc_link_pattern, index_html, re.IGNORECASE)
            
            for match in matches:
                url = match.group(1)
                description = match.group(2).strip()
                
                # Determine document type from filename or description
                filename = url.split("/")[-1] if "/" in url else url
                doc_type = None
                
                # Try to extract document type from description or filename
                if "10-Q" in description.upper() or "10-Q" in filename.upper():
                    doc_type = "10-Q"
                elif "10-K" in description.upper() or "10-K" in filename.upper():
                    doc_type = "10-K"
                elif "8-K" in description.upper() or "8-K" in filename.upper():
                    doc_type = "8-K"
                elif filename.startswith("EX-") or "EX-" in filename:
                    # Extract exhibit number
                    ex_match = re.search(r'EX-(\d+\.\d+)', filename, re.IGNORECASE)
                    if ex_match:
                        doc_type = f"EX-{ex_match.group(1)}"
                elif filename.endswith(".xml"):
                    doc_type = "XML"
                elif filename.endswith(".txt"):
                    doc_type = "TXT"
                
                # Build full URL if relative
                if url.startswith("http"):
                    full_url = url
                elif base_url:
                    full_url = base_url.rstrip("/") + "/" + url.lstrip("/")
                else:
                    full_url = url
                
                documents.append({
                    "filename": filename,
                    "description": description,
                    "type": doc_type or "Unknown",
                    "url": full_url
                })
            
            result = {
                "data": documents,
                "source_urls": [],
                "warnings": [] if documents else ["No documents found in index HTML"]
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": [],
                "source_urls": [],
                "warnings": [f"Failed to parse filing index: {str(e)}"]
            })


class FindDocumentByTypeInput(BaseModel):
    """Input schema for find_document_by_type tool."""
    documents: str = Field(
        ...,
        description="JSON string of document list from parse_filing_index_documents"
    )
    preferred_types: List[str] = Field(
        ...,
        description="List of preferred document types (e.g., ['10-Q', '10-K', 'EX-99.1'])"
    )


class FindDocumentByTypeTool(BaseTool):
    """
    Find documents by preferred types.
    
    Searches through a list of documents and returns the best matches
    for the preferred document types.
    """
    name: str = "find_document_by_type"
    description: str = """
    Finds documents from a filing that match preferred types. Returns the
    best matches along with rationale. Useful for finding specific forms
    or exhibits (e.g., 10-Q, 10-K, EX-99.1, EX-101.INS).
    """
    args_schema: Type[BaseModel] = FindDocumentByTypeInput

    def _run(self, documents: str, preferred_types: List[str]) -> str:
        try:
            # Parse documents
            if isinstance(documents, str):
                docs = json.loads(documents)
            else:
                docs = documents
            
            if not isinstance(docs, list):
                return json.dumps({
                    "data": [],
                    "source_urls": [],
                    "warnings": ["Documents must be a list"]
                })
            
            # Normalize preferred types to uppercase
            preferred_upper = [pt.upper() for pt in preferred_types]
            
            matches = []
            for doc in docs:
                doc_type = doc.get("type", "").upper()
                filename = doc.get("filename", "").upper()
                description = doc.get("description", "").upper()
                
                # Check if document matches any preferred type
                for pref_type in preferred_upper:
                    if (pref_type in doc_type or 
                        pref_type in filename or 
                        pref_type in description):
                        matches.append({
                            "document": doc,
                            "matched_type": pref_type,
                            "rationale": f"Matched {pref_type} in type/filename/description"
                        })
                        break
            
            result = {
                "data": {
                    "matches": matches,
                    "total_documents": len(docs),
                    "matches_found": len(matches)
                },
                "source_urls": [],
                "warnings": [] if matches else [f"No documents found matching types: {preferred_types}"]
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": [],
                "source_urls": [],
                "warnings": ["Invalid JSON in documents parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": [],
                "source_urls": [],
                "warnings": [f"Failed to find documents by type: {str(e)}"]
            })


class DownloadFilingDocumentInput(BaseModel):
    """Input schema for download_filing_document tool."""
    doc_url: str = Field(..., description="URL of the document to download")
    dest_path: str = Field(..., description="Local path where to save the document")


class DownloadFilingDocumentTool(BaseTool):
    """
    Download a filing document.
    
    Downloads any document from a filing (HTML, TXT, XML, PDF) to a local path.
    """
    name: str = "download_filing_document"
    description: str = """
    Downloads a filing document from EDGAR to a local path. Supports HTML,
    TXT, XML, and PDF files. Returns the path to the downloaded file.
    """
    args_schema: Type[BaseModel] = DownloadFilingDocumentInput

    def _run(self, doc_url: str, dest_path: str) -> str:
        client = get_default_client()
        
        try:
            downloaded_path = client.download(doc_url, dest_path)
            
            result = {
                "data": {
                    "downloaded_path": downloaded_path,
                    "url": doc_url,
                    "file_size": Path(downloaded_path).stat().st_size if Path(downloaded_path).exists() else None
                },
                "source_urls": [doc_url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [doc_url],
                "warnings": [f"Failed to download document: {str(e)}"]
            })


class GetCompleteSubmissionTextInput(BaseModel):
    """Input schema for get_complete_submission_text tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    accession_with_dashes: str = Field(
        ...,
        description="Accession number with dashes (e.g., '0000320193-25-000010')"
    )


class GetCompleteSubmissionTextTool(BaseTool):
    """
    Get complete submission text file.
    
    Fetches the complete submission text file (.txt) which contains the
    entire filing in text format. Useful fallback when index parsing fails.
    """
    name: str = "get_complete_submission_text"
    description: str = """
    Fetches the complete submission text file for a filing. This is a single
    text file containing the entire filing. Useful as a fallback when the
    filing index parsing fails or when you need the raw text content.
    """
    args_schema: Type[BaseModel] = GetCompleteSubmissionTextInput

    def _run(self, cik: str, accession_with_dashes: str) -> str:
        client = get_default_client()
        
        # Build URL
        url_tool = BuildCompleteSubmissionTxtUrlTool()
        url_result = json.loads(url_tool._run(cik, accession_with_dashes))
        url = url_result["data"]["url"]
        
        try:
            response = client.get(url)
            text_content = response.text
            
            result = {
                "data": {
                    "text": text_content,
                    "url": url,
                    "length": len(text_content)
                },
                "source_urls": [url],
                "warnings": []
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "data": None,
                "source_urls": [url],
                "warnings": [f"Failed to fetch complete submission text: {str(e)}"]
            })
