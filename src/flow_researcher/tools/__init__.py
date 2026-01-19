"""
SEC Tools for CrewAI Financial Analyst Crew.

This package provides tools for accessing SEC data including:
- Company identity and lookup
- Filing discovery and metadata
- EDGAR URL construction
- Filing document retrieval
- XBRL financial data
- EDGAR index files
- Bulk data downloads
- RSS monitoring
- Higher-level convenience tools
- HTTP client with rate limiting and caching
"""

from .sec_http_client import SECHttpClient, get_default_client, set_default_client

from .company_tools import (
    GetTickerCikMapTool,
    TickerToCikTool,
    GetCompanySubmissionsTool,
    GetCompanyProfileTool,
)

from .filing_tools import (
    ListRecentFilingsTool,
    GetLatestFilingTool,
    GetFilingsByDateRangeTool,
    GetFilingAcceptanceDatetimeTool,
)

from .edgar_url_tools import (
    AccessionToNodashesTool,
    BuildFilingIndexUrlTool,
    BuildCompleteSubmissionTxtUrlTool,
    BuildFilingFolderUrlTool,
)

from .filing_document_tools import (
    GetFilingIndexHtmlTool,
    ParseFilingIndexDocumentsTool,
    FindDocumentByTypeTool,
    DownloadFilingDocumentTool,
    GetCompleteSubmissionTextTool,
)

from .xbrl_tools import (
    GetCompanyFactsTool,
    ListTaxonomiesTool,
    ListConceptsTool,
    GetCompanyConceptTool,
    GetFramesTool,
    NormalizeFactsToTableTool,
    FactsFilterTool,
)

from .edgar_index_tools import (
    ListDailyIndexPathsTool,
    DownloadDailyMasterIndexTool,
    ParseMasterIdxTool,
    FindFilingsInMasterIdxTool,
    EdgarPathToDocUrlTool,
)

from .bulk_data_tools import (
    DownloadBulkSubmissionsZipTool,
    DownloadBulkCompanyfactsZipTool,
    ExtractBulkZipTool,
)

from .rss_tools import (
    GetCompanyEdgarRssFeedUrlTool,
    FetchRssTool,
    RssItemsToFilingsTool,
)

from .convenience_tools import (
    GetLatest10qOr10kTool,
    GetLatest8kTool,
    GetFilingDocsBundleTool,
    GetKeyFinancialSeriesTool,
)

__all__ = [
    # HTTP Client
    "SECHttpClient",
    "get_default_client",
    "set_default_client",
    # Company Tools
    "GetTickerCikMapTool",
    "TickerToCikTool",
    "GetCompanySubmissionsTool",
    "GetCompanyProfileTool",
    # Filing Tools
    "ListRecentFilingsTool",
    "GetLatestFilingTool",
    "GetFilingsByDateRangeTool",
    "GetFilingAcceptanceDatetimeTool",
    # EDGAR URL Tools
    "AccessionToNodashesTool",
    "BuildFilingIndexUrlTool",
    "BuildCompleteSubmissionTxtUrlTool",
    "BuildFilingFolderUrlTool",
    # Filing Document Tools
    "GetFilingIndexHtmlTool",
    "ParseFilingIndexDocumentsTool",
    "FindDocumentByTypeTool",
    "DownloadFilingDocumentTool",
    "GetCompleteSubmissionTextTool",
    # XBRL Tools
    "GetCompanyFactsTool",
    "ListTaxonomiesTool",
    "ListConceptsTool",
    "GetCompanyConceptTool",
    "GetFramesTool",
    "NormalizeFactsToTableTool",
    "FactsFilterTool",
    # EDGAR Index Tools
    "ListDailyIndexPathsTool",
    "DownloadDailyMasterIndexTool",
    "ParseMasterIdxTool",
    "FindFilingsInMasterIdxTool",
    "EdgarPathToDocUrlTool",
    # Bulk Data Tools
    "DownloadBulkSubmissionsZipTool",
    "DownloadBulkCompanyfactsZipTool",
    "ExtractBulkZipTool",
    # RSS Tools
    "GetCompanyEdgarRssFeedUrlTool",
    "FetchRssTool",
    "RssItemsToFilingsTool",
    # Convenience Tools
    "GetLatest10qOr10kTool",
    "GetLatest8kTool",
    "GetFilingDocsBundleTool",
    "GetKeyFinancialSeriesTool",
]
