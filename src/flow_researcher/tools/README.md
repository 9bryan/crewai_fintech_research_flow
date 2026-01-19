# SEC Tools for CrewAI

A comprehensive set of tools for accessing SEC (Securities and Exchange Commission) data through the EDGAR system. These tools provide access to company information, filings, financial data, and more.

## Overview

This package provides tools organized into several categories:

- **HTTP Client**: Rate-limited, cached HTTP client for SEC APIs
- **Company Tools**: Company identity and lookup
- **Filing Tools**: Filing discovery and metadata
- **EDGAR URL Tools**: URL construction for EDGAR resources
- **Filing Document Tools**: Document retrieval and parsing
- **XBRL Tools**: Structured financial data (XBRL facts)
- **EDGAR Index Tools**: Daily/quarterly index file access
- **Bulk Data Tools**: Download and extract bulk data files
- **RSS Tools**: RSS feed monitoring
- **Convenience Tools**: High-level composite tools

## Installation

The tools are part of the `flow_researcher` package. Install dependencies:

```bash
uv sync
```

## HTTP Client

The `SECHttpClient` provides rate-limited, cached HTTP access to SEC APIs.

### Basic Usage

```python
from flow_researcher.tools.sec_http_client import SECHttpClient

client = SECHttpClient(
    user_agent="YourApp yourname@example.com",
    max_requests_per_second=10.0,
    cache_ttl_seconds=3600
)

# GET request with caching
response = client.get("https://data.sec.gov/submissions/CIK0000320193.json")
data = response.json()

# Download file
client.download("https://www.sec.gov/Archives/edgar/data/...", "/path/to/file.txt")
```

## Company Tools

Tools for company identity and lookup.

### GetTickerCikMapTool

Get the complete ticker-to-CIK mapping from SEC.

```python
from flow_researcher.tools import GetTickerCikMapTool

tool = GetTickerCikMapTool()
result = tool._run()
# Returns: {"data": {...}, "source_urls": [...], "warnings": []}
```

### TickerToCikTool

Convert a stock ticker symbol to CIK number.

```python
from flow_researcher.tools import TickerToCikTool

tool = TickerToCikTool()
result = tool._run("AAPL")
# Returns: {"data": {"ticker": "AAPL", "cik": "0000320193", "company_name": "Apple Inc."}, ...}
```

### GetCompanySubmissionsTool

Get company submissions history (metadata + recent filings).

```python
from flow_researcher.tools import GetCompanySubmissionsTool

tool = GetCompanySubmissionsTool()
result = tool._run("0000320193")  # CIK for Apple
# Returns: {"data": {"name": "...", "filings": {...}}, ...}
```

### GetCompanyProfileTool

Get normalized company profile from ticker.

```python
from flow_researcher.tools import GetCompanyProfileTool

tool = GetCompanyProfileTool()
result = tool._run("AAPL")
# Returns: {"data": {"ticker": "AAPL", "cik": "0000320193", "entity_name": "...", ...}, ...}
```

## Filing Tools

Tools for discovering and retrieving filing metadata.

### ListRecentFilingsTool

List recent filings for a company, optionally filtered by form type.

```python
from flow_researcher.tools import ListRecentFilingsTool

tool = ListRecentFilingsTool()
result = tool._run(
    cik="0000320193",
    forms=["10-Q", "10-K"],  # Optional: filter by form types
    limit=10  # Optional: max number of filings
)
# Returns: {"data": [{"form": "10-Q", "filingDate": "...", ...}, ...], ...}
```

### GetLatestFilingTool

Get the most recent filing of a specific form type.

```python
from flow_researcher.tools import GetLatestFilingTool

tool = GetLatestFilingTool()
result = tool._run("0000320193", "10-Q")
# Returns: {"data": {"form": "10-Q", "filingDate": "...", "accessionNumber": "...", ...}, ...}
```

### GetFilingsByDateRangeTool

Get filings within a date range.

```python
from flow_researcher.tools import GetFilingsByDateRangeTool

tool = GetFilingsByDateRangeTool()
result = tool._run(
    cik="0000320193",
    start_date="2024-01-01",
    end_date="2024-12-31",
    forms=["10-Q"]  # Optional
)
# Returns: {"data": [filing1, filing2, ...], ...}
```

### GetFilingAcceptanceDatetimeTool

Extract acceptance datetime from filing metadata.

```python
from flow_researcher.tools import GetFilingAcceptanceDatetimeTool
import json

tool = GetFilingAcceptanceDatetimeTool()
filing_meta = json.dumps({"acceptanceDateTime": "2024-01-15T16:30:00-05:00", ...})
result = tool._run(filing_meta)
# Returns: {"data": {"acceptanceDateTime": "...", "iso_format": "..."}, ...}
```

## EDGAR URL Tools

Tools for constructing EDGAR archive URLs.

### AccessionToNodashesTool

Convert accession number from dashed to no-dashes format.

```python
from flow_researcher.tools import AccessionToNodashesTool

tool = AccessionToNodashesTool()
result = tool._run("0000320193-25-000010")
# Returns: {"data": {"accession_with_dashes": "...", "accession_no_dashes": "000032019325000010"}, ...}
```

### BuildFilingIndexUrlTool

Build URL for filing index HTML page.

```python
from flow_researcher.tools import BuildFilingIndexUrlTool

tool = BuildFilingIndexUrlTool()
result = tool._run("0000320193", "0000320193-25-000010")
# Returns: {"data": {"url": "https://www.sec.gov/Archives/edgar/data/.../...-index.html", ...}, ...}
```

### BuildCompleteSubmissionTxtUrlTool

Build URL for complete submission text file.

```python
from flow_researcher.tools import BuildCompleteSubmissionTxtUrlTool

tool = BuildCompleteSubmissionTxtUrlTool()
result = tool._run("0000320193", "0000320193-25-000010")
# Returns: {"data": {"url": "https://www.sec.gov/Archives/edgar/data/.../....txt", ...}, ...}
```

### BuildFilingFolderUrlTool

Build base URL for filing folder/directory.

```python
from flow_researcher.tools import BuildFilingFolderUrlTool

tool = BuildFilingFolderUrlTool()
result = tool._run("0000320193", "0000320193-25-000010")
# Returns: {"data": {"url": "https://www.sec.gov/Archives/edgar/data/.../.../", ...}, ...}
```

## Filing Document Tools

Tools for retrieving and parsing filing documents.

### GetFilingIndexHtmlTool

Get the HTML index page for a filing.

```python
from flow_researcher.tools import GetFilingIndexHtmlTool

tool = GetFilingIndexHtmlTool()
result = tool._run("0000320193", "0000320193-25-000010")
# Returns: {"data": {"html": "<html>...", "url": "..."}, ...}
```

### ParseFilingIndexDocumentsTool

Parse filing index HTML into a list of documents.

```python
from flow_researcher.tools import ParseFilingIndexDocumentsTool

tool = ParseFilingIndexDocumentsTool()
result = tool._run(index_html)  # HTML from GetFilingIndexHtmlTool
# Returns: {"data": [{"filename": "...", "type": "10-Q", "url": "...", ...}, ...], ...}
```

### FindDocumentByTypeTool

Find documents matching preferred types.

```python
from flow_researcher.tools import FindDocumentByTypeTool
import json

tool = FindDocumentByTypeTool()
documents = json.dumps([{"filename": "...", "type": "10-Q", ...}, ...])
result = tool._run(documents, ["10-Q", "EX-99.1"])
# Returns: {"data": {"matches": [...], "matches_found": 2, ...}, ...}
```

### DownloadFilingDocumentTool

Download a filing document to local path.

```python
from flow_researcher.tools import DownloadFilingDocumentTool

tool = DownloadFilingDocumentTool()
result = tool._run(
    doc_url="https://www.sec.gov/Archives/edgar/data/.../file.html",
    dest_path="/path/to/downloaded/file.html"
)
# Returns: {"data": {"downloaded_path": "...", "file_size": 12345}, ...}
```

### GetCompleteSubmissionTextTool

Get the complete submission text file.

```python
from flow_researcher.tools import GetCompleteSubmissionTextTool

tool = GetCompleteSubmissionTextTool()
result = tool._run("0000320193", "0000320193-25-000010")
# Returns: {"data": {"text": "...", "url": "...", "length": 12345}, ...}
```

## XBRL Tools

Tools for accessing structured financial data (XBRL facts).

### GetCompanyFactsTool

Get complete company facts (all XBRL data).

```python
from flow_researcher.tools import GetCompanyFactsTool

tool = GetCompanyFactsTool()
result = tool._run("0000320193")
# Returns: {"data": {"facts": {"us-gaap": {...}, "dei": {...}, ...}}, ...}
```

### ListTaxonomiesTool

List available taxonomies in company facts.

```python
from flow_researcher.tools import ListTaxonomiesTool
import json

tool = ListTaxonomiesTool()
companyfacts_json = json.dumps({...})  # From GetCompanyFactsTool
result = tool._run(companyfacts_json)
# Returns: {"data": {"taxonomies": ["us-gaap", "dei", ...], "count": 3}, ...}
```

### ListConceptsTool

List available XBRL concepts/tags in a taxonomy.

```python
from flow_researcher.tools import ListConceptsTool
import json

tool = ListConceptsTool()
companyfacts_json = json.dumps({...})  # From GetCompanyFactsTool
result = tool._run(companyfacts_json, taxonomy="us-gaap")
# Returns: {"data": {"taxonomy": "us-gaap", "concepts": ["Revenues", "Assets", ...], ...}, ...}
```

### GetCompanyConceptTool

Get time-series data for a single XBRL concept/tag.

```python
from flow_researcher.tools import GetCompanyConceptTool

tool = GetCompanyConceptTool()
result = tool._run("0000320193", "us-gaap", "Revenues")
# Returns: {"data": {"units": {"USD": [{"val": 1234567890, "end": "2024-09-28", ...}, ...]}}, ...}
```

### GetFramesTool

Get cross-company frame (same concept across multiple companies).

```python
from flow_researcher.tools import GetFramesTool

tool = GetFramesTool()
result = tool._run("us-gaap", "Revenues", "USD", "CY2023")
# Returns: {"data": {"data": [{"cik": "...", "val": ..., ...}, ...]}, ...}
```

### NormalizeFactsToTableTool

Convert company facts to normalized tabular format.

```python
from flow_researcher.tools import NormalizeFactsToTableTool
import json

tool = NormalizeFactsToTableTool()
companyfacts_json = json.dumps({...})  # From GetCompanyFactsTool
result = tool._run(companyfacts_json, taxonomy="us-gaap")
# Returns: {"data": {"rows": [{"tag": "Revenues", "unit": "USD", "fy": 2024, "val": ..., ...}, ...], ...}, ...}
```

### FactsFilterTool

Filter normalized facts rows by various criteria.

```python
from flow_researcher.tools import FactsFilterTool
import json

tool = FactsFilterTool()
rows = json.dumps({"rows": [...], ...})  # From NormalizeFactsToTableTool
result = tool._run(
    rows=rows,
    tag="Revenues",  # Optional
    fp="Q1",  # Optional: fiscal period
    form="10-Q",  # Optional: form type
    unit="USD",  # Optional
    start_end="2024-01-01:2024-12-31"  # Optional: date range
)
# Returns: {"data": {"rows": [filtered rows], "count": 5, ...}, ...}
```

## EDGAR Index Tools

Tools for working with EDGAR daily/quarterly index files.

### ListDailyIndexPathsTool

List daily index file paths for a year/quarter.

```python
from flow_researcher.tools import ListDailyIndexPathsTool

tool = ListDailyIndexPathsTool()
result = tool._run(2024, quarter=1)  # Optional quarter
# Returns: {"data": {"year": 2024, "quarter": 1, "paths": ["...", ...], ...}, ...}
```

### DownloadDailyMasterIndexTool

Download daily master index file.

```python
from flow_researcher.tools import DownloadDailyMasterIndexTool

tool = DownloadDailyMasterIndexTool()
result = tool._run("2024-01-15", "/path/to/master.idx")
# Returns: {"data": {"downloaded_path": "...", "url": "...", "date": "2024-01-15"}, ...}
```

### ParseMasterIdxTool

Parse master index file into rows.

```python
from flow_researcher.tools import ParseMasterIdxTool

tool = ParseMasterIdxTool()
result = tool._run("/path/to/master.idx")
# Returns: {"data": {"rows": [{"cik": "...", "company_name": "...", "form_type": "...", ...}, ...], ...}, ...}
```

### FindFilingsInMasterIdxTool

Filter master index rows by CIK and/or form types.

```python
from flow_researcher.tools import FindFilingsInMasterIdxTool
import json

tool = FindFilingsInMasterIdxTool()
rows = json.dumps({"rows": [...], ...})  # From ParseMasterIdxTool
result = tool._run(rows, cik="0000320193", forms=["10-Q", "10-K"])
# Returns: {"data": {"rows": [filtered rows], "count": 5, ...}, ...}
```

### EdgarPathToDocUrlTool

Convert EDGAR path to full URL.

```python
from flow_researcher.tools import EdgarPathToDocUrlTool

tool = EdgarPathToDocUrlTool()
result = tool._run("edgar/data/320193/000032019325000010/file.html")
# Returns: {"data": {"url": "https://www.sec.gov/Archives/edgar/data/...", ...}, ...}
```

## Bulk Data Tools

Tools for downloading and extracting bulk data files.

### DownloadBulkSubmissionsZipTool

Download bulk submissions ZIP file.

```python
from flow_researcher.tools import DownloadBulkSubmissionsZipTool

tool = DownloadBulkSubmissionsZipTool()
result = tool._run("/path/to/submissions.zip")
# Returns: {"data": {"downloaded_path": "...", "file_size": 123456789}, ...}
```

### DownloadBulkCompanyfactsZipTool

Download bulk company facts ZIP file.

```python
from flow_researcher.tools import DownloadBulkCompanyfactsZipTool

tool = DownloadBulkCompanyfactsZipTool()
result = tool._run("/path/to/companyfacts.zip")
# Returns: {"data": {"downloaded_path": "...", "file_size": 123456789}, ...}
```

### ExtractBulkZipTool

Extract bulk ZIP file into JSON files.

```python
from flow_researcher.tools import ExtractBulkZipTool

tool = ExtractBulkZipTool()
result = tool._run("/path/to/file.zip", "/path/to/extract/dir")
# Returns: {"data": {"dest_dir": "...", "extracted_files": [...], "file_count": 123}, ...}
```

## RSS Tools

Tools for RSS feed monitoring.

### GetCompanyEdgarRssFeedUrlTool

Get company EDGAR RSS feed URL.

```python
from flow_researcher.tools import GetCompanyEdgarRssFeedUrlTool

tool = GetCompanyEdgarRssFeedUrlTool()
result = tool._run("0000320193")
# Returns: {"data": {"url": "https://www.sec.gov/cgi-bin/browse-edgar?...&output=atom", ...}, ...}
```

### FetchRssTool

Fetch and parse RSS/Atom feed.

```python
from flow_researcher.tools import FetchRssTool

tool = FetchRssTool()
result = tool._run("https://www.sec.gov/cgi-bin/browse-edgar?...&output=atom")
# Returns: {"data": {"items": [{"title": "...", "link": "...", "pubDate": "...", ...}, ...], ...}, ...}
```

### RssItemsToFilingsTool

Extract filing information from RSS items.

```python
from flow_researcher.tools import RssItemsToFilingsTool
import json

tool = RssItemsToFilingsTool()
items = json.dumps({"items": [...], ...})  # From FetchRssTool
result = tool._run(items)
# Returns: {"data": {"filings": [{"cik": "...", "accession": "...", "form": "10-Q", ...}, ...], ...}, ...}
```

## Convenience Tools

High-level tools that combine multiple operations.

### GetLatest10qOr10kTool

Get the most recent 10-Q or 10-K filing.

```python
from flow_researcher.tools import GetLatest10qOr10kTool

tool = GetLatest10qOr10kTool()
result = tool._run("AAPL")
# Returns: {"data": {"form": "10-Q", "filingDate": "...", ...}, ...}
```

### GetLatest8kTool

Get the most recent 8-K filing.

```python
from flow_researcher.tools import GetLatest8kTool

tool = GetLatest8kTool()
result = tool._run("AAPL")
# Returns: {"data": {"form": "8-K", "filingDate": "...", ...}, ...}
```

### GetFilingDocsBundleTool

Get complete filing documents bundle (metadata + document index).

```python
from flow_researcher.tools import GetFilingDocsBundleTool

tool = GetFilingDocsBundleTool()
result = tool._run("AAPL", "10-Q")
# Returns: {"data": {"filing_meta": {...}, "documents": [...], "document_count": 5, ...}, ...}
```

### GetKeyFinancialSeriesTool

Get time-series financial data for multiple XBRL tags.

```python
from flow_researcher.tools import GetKeyFinancialSeriesTool

tool = GetKeyFinancialSeriesTool()
result = tool._run("AAPL", ["Revenues", "NetIncomeLoss", "Assets"])
# Returns: {"data": {"ticker": "AAPL", "series": {"Revenues": {...}, ...}, ...}, ...}
```

## Using Tools in CrewAI Agents

To use these tools in a CrewAI agent:

```python
from crewai import Agent
from flow_researcher.tools import TickerToCikTool, GetCompanyFactsTool, ListRecentFilingsTool

agent = Agent(
    role="Financial Analyst",
    goal="Analyze company financial data",
    tools=[
        TickerToCikTool(),
        GetCompanyFactsTool(),
        ListRecentFilingsTool(),
    ],
    verbose=True
)
```

## Return Format

All tools return a JSON string with this structure:

```python
{
    "data": <tool-specific data>,
    "source_urls": ["url1", "url2", ...],
    "warnings": ["warning1", "warning2", ...]
}
```

- `data`: The main result (varies by tool)
- `source_urls`: List of URLs used to fetch data
- `warnings`: List of non-fatal issues or messages

## Rate Limiting & Caching

All tools use the shared `SECHttpClient` which:
- Enforces ≤10 requests/second (SEC fair access requirement)
- Caches responses (default TTL: 1 hour)
- Sends proper User-Agent headers
- Handles retries automatically

## Error Handling

Tools return warnings in the `warnings` field for non-fatal issues. If `data` is `None`, check `warnings` for error details.

## Testing

Run tests with:

```bash
uv run pytest tests/ -v
```

Tests are organized by module (e.g., `test_company_tools.py` for `company_tools.py`).

## Documentation

For detailed specifications, see `sec_tools_spec.md` in this directory.
