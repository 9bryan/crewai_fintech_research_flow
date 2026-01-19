# SEC / data.sec.gov Tooling Catalog (Single-Ticker Operations)

This document defines an **atomic tool/function list** for an agent that can perform essentially all common operations available via **sec.gov** and **data.sec.gov** public data APIs and EDGAR archives.  
It is designed for implementation in Cursor as a library of small, composable functions.

> **Fair Access Requirements (apply to every HTTP tool)**
- Enforce **<= 10 requests/second**. :contentReference[oaicite:0]{index=0}  
- Send a descriptive `User-Agent` header (e.g., `YourCompany yourname@domain.com`). :contentReference[oaicite:1]{index=1}  
- Prefer caching and “download only what you need.” :contentReference[oaicite:2]{index=2}  
- These APIs are public and generally do **not** require API keys. :contentReference[oaicite:3]{index=3}  

---

## 0) Shared Types / Conventions

### Types
- `CIK`: 10-digit, zero-padded string (e.g., `"0000789019"`)
- `AccessionWithDashes`: e.g., `"0000320193-25-000010"`
- `AccessionNoDashes`: e.g., `"000032019325000010"`
- `EdgarDocUrl`: any URL under `https://www.sec.gov/Archives/edgar/...`

### Conventions
- Every tool returns:
  - `data` (structured result)
  - `source_urls` (list of URLs used)
  - `warnings` (list of non-fatal issues)
- Every network tool accepts:
  - `http: { timeout_s, user_agent, cache_ttl_s, max_rps }`

---

## 1) HTTP + Rate-Limit + Cache Primitives (must-have)

### 1.1 `sec_http_get(url, headers={}, params={})` ✅
- Purpose: single GET with fair-access headers, retries, caching, gzip support.
- **Implementation**: `SECHttpClient.get()` in `sec_http_client.py`

### 1.2 `sec_http_download(url, dest_path)` ✅
- Purpose: download filing docs (HTML, TXT, XML, PDF) from `sec.gov/Archives/...`.
- **Implementation**: `SECHttpClient.download()` in `sec_http_client.py`

### 1.3 `sec_rate_limiter.configure(max_requests_per_second=10)` ✅
- Enforce SEC fair access limit. :contentReference[oaicite:4]{index=4}  
- **Implementation**: `RateLimiter` class in `sec_http_client.py`, configured via `SECHttpClient` constructor

### 1.4 `sec_cache.get(key)` / `sec_cache.set(key, value, ttl_s)` ✅
- Local cache for JSON responses and downloaded docs.
- **Implementation**: `SimpleCache` class in `sec_http_client.py`, used by `SECHttpClient`

---

## 2) Company Identity & Lookup Tools

### 2.1 `get_ticker_cik_map()` ✅
- Source:
  - `https://www.sec.gov/files/company_tickers_exchange.json`
- Returns: list/map of `{ ticker, cik, name, exchange }`
- **Implementation**: `GetTickerCikMapTool` in `company_tools.py`

### 2.2 `ticker_to_cik(ticker)` ✅
- Uses: `get_ticker_cik_map()`
- Returns: `CIK` (10-digit padded string)
- **Implementation**: `TickerToCikTool` in `company_tools.py`

### 2.3 `get_company_submissions(cik)`
- Source:
  - `https://data.sec.gov/submissions/CIK##########.json` :contentReference[oaicite:5]{index=5}  
- Returns: SEC “submissions history” JSON (company metadata + recent filings arrays)

### 2.4 `get_company_profile(ticker)` ✅
- Derived from `submissions` JSON:
  - entity name, former names, tickers/exchanges, SIC, addresses, filer flags, etc.
- Returns: normalized `CompanyProfile`
- **Implementation**: `GetCompanyProfileTool` in `company_tools.py`

---

## 3) Filings Discovery & Metadata Tools

> The submissions API provides at least ~1 year / up to 1000 of most recent filings, and may reference additional JSON for older ranges. :contentReference[oaicite:6]{index=6}  

### 3.1 `list_recent_filings(cik, forms=None, limit=100)` ✅
- Inputs:
  - `forms`: e.g., `["10-Q","10-K","8-K","20-F","6-K"]`
- Uses: `get_company_submissions(cik)`
- Returns: list of normalized `FilingMeta`:
  - `form`, `filingDate`, `reportDate`, `acceptanceDateTime` (if present), `accessionNumber`, `primaryDocument`, etc.
- **Implementation**: `ListRecentFilingsTool` in `filing_tools.py`

### 3.2 `get_latest_filing(cik, form)` ✅
- Returns: single `FilingMeta` for the most recent matching form.
- **Implementation**: `GetLatestFilingTool` in `filing_tools.py`

### 3.3 `get_filings_by_date_range(cik, start_date, end_date, forms=None)`
- Uses: `submissions` + any referenced “additional filings” JSON files if present.
- Returns: filings in date range.

### 3.4 `get_filing_acceptance_datetime(filing_meta)`
- Extract acceptance timestamp where available (useful for “when filed” timing).
- Returns: ISO datetime or warning if unavailable.

---

## 4) EDGAR Archive URL Construction Tools

### 4.1 `accession_to_nodashes(accession_with_dashes)` ✅
- Returns: `AccessionNoDashes`
- **Implementation**: `AccessionToNodashesTool` in `edgar_url_tools.py`

### 4.2 `build_filing_index_url(cik, accession_with_dashes)` ✅
- Returns:
  - `https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-WITH-DASHES}-index.html`
- **Implementation**: `BuildFilingIndexUrlTool` in `edgar_url_tools.py`

### 4.3 `build_complete_submission_txt_url(cik, accession_with_dashes)` ✅
- Returns (common pattern):
  - `https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-WITH-DASHES}.txt`
- **Implementation**: `BuildCompleteSubmissionTxtUrlTool` in `edgar_url_tools.py`

### 4.4 `build_filing_folder_url(cik, accession_with_dashes)` ✅
- Returns:
  - `https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-NO-DASHES}/`
- **Implementation**: `BuildFilingFolderUrlTool` in `edgar_url_tools.py`

---

## 5) Filing Document Index & Retrieval Tools

### 5.1 `get_filing_index_html(cik, accession_with_dashes)`
- Fetches:
  - `{ACCESSION}-index.html`
- Returns: raw HTML.

### 5.2 `parse_filing_index_documents(index_html)`
- Parses the index page into a list of documents:
  - `filename`, `description`, `type` (e.g., EX-99.1, 10-Q, XML), `url`, `size`, etc.
- Returns: `FilingDocument[]`

### 5.3 `find_document_by_type(documents, preferred_types)`
- Example `preferred_types`:
  - `["10-Q","10-K","8-K","EX-99.1","EX-99.2","EX-101.INS","EX-101.SCH"]`
- Returns: best-match doc(s) + rationale.

### 5.4 `download_filing_document(doc_url, dest_path)`
- Downloads any doc from the filing folder (HTML/TXT/XML/PDF).

### 5.5 `get_complete_submission_text(cik, accession_with_dashes)`
- Fetches the “.txt” complete submission (if available) and returns text.
- Useful fallback when index parsing fails.

---

## 6) XBRL “Facts” APIs (Structured Financial Data)

> SEC’s EDGAR APIs include extracted XBRL data for financial statements and provide company submissions history. :contentReference[oaicite:7]{index=7}  

### 6.1 `get_company_facts(cik)` ✅
- Source:
  - `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` :contentReference[oaicite:8]{index=8}  
- Returns: raw `companyfacts` JSON.
- **Implementation**: `GetCompanyFactsTool` in `xbrl_tools.py`

### 6.2 `list_taxonomies(companyfacts_json)` ✅
- Returns: available taxonomies (`us-gaap`, `dei`, `ifrs-full`, `srt`, etc.). :contentReference[oaicite:9]{index=9}  
- **Implementation**: `ListTaxonomiesTool` in `xbrl_tools.py`

### 6.3 `list_concepts(companyfacts_json, taxonomy="us-gaap")` ✅
- Returns: list of available tags/concepts for the company within a taxonomy.
- **Implementation**: `ListConceptsTool` in `xbrl_tools.py`

### 6.4 `get_company_concept(cik, taxonomy, tag)` ✅
- Source pattern:
  - `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/{taxonomy}/{tag}.json` :contentReference[oaicite:10]{index=10}  
- Returns: time-series fact data for a single concept (e.g., all reported `Revenues`).
- **Implementation**: `GetCompanyConceptTool` in `xbrl_tools.py`

### 6.5 `get_frames(taxonomy, tag, unit, period)` ✅
- Source pattern:
  - `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json` :contentReference[oaicite:11]{index=11}  
- Purpose: cross-company frame; still useful for validation or peer comps.
- **Implementation**: `GetFramesTool` in `xbrl_tools.py`

### 6.6 `normalize_facts_to_table(companyfacts_json, taxonomy="us-gaap")` ✅
- Returns: tabular rows:
  - `tag`, `unit`, `fy`, `fp`, `end`, `val`, `form`, `filed`, `frame`, `accn`
- (Keep `accn` to join back to filings/documents.)
- **Implementation**: `NormalizeFactsToTableTool` in `xbrl_tools.py`

### 6.7 `facts_filter(rows, tag=None, fp=None, form=None, unit=None, start_end=None)` ✅
- Small helper to query normalized facts.
- **Implementation**: `FactsFilterTool` in `xbrl_tools.py`

---

## 7) EDGAR Index Files (Daily / Quarterly / Full)

These indexes are useful when you want to:
- find filings by date for “latest filings”
- build your own search without relying on submissions JSON
- ensure you don’t miss something the submissions endpoint didn’t surface (edge cases)

Directory roots:
- Daily:
  - `https://www.sec.gov/Archives/edgar/daily-index/` :contentReference[oaicite:12]{index=12}  
- Full / Quarterly:
  - `https://www.sec.gov/Archives/edgar/full-index/` :contentReference[oaicite:13]{index=13}  

### 7.1 `list_daily_index_paths(year, quarter=None)`
- Enumerate likely `.idx`, `.gz`, `.zip` targets under daily-index.

### 7.2 `download_daily_master_index(date, dest_path)`
- Fetch that day’s `master.idx` (or zipped/gz variants) when available.

### 7.3 `parse_master_idx(file_path)`
- Returns rows with:
  - `cik`, `company_name`, `form_type`, `date_filed`, `edgar_path`

### 7.4 `find_filings_in_master_idx(rows, cik=None, forms=None)`
- Filter for single company and form types.

### 7.5 `edgar_path_to_doc_url(edgar_path)`
- Converts `edgar/data/...` paths from indexes into `https://www.sec.gov/Archives/...` URLs.

---

## 8) Bulk Data (Nightly ZIPs)

SEC provides bulk ZIPs for submissions and XBRL facts updated nightly. :contentReference[oaicite:14]{index=14}  

### 8.1 `download_bulk_submissions_zip(dest_path)` ✅
- Source (from SEC docs / EDGAR bulk directories):
  - `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` :contentReference[oaicite:15]{index=15}  
- **Implementation**: `DownloadBulkSubmissionsZipTool` in `bulk_data_tools.py`

### 8.2 `download_bulk_companyfacts_zip(dest_path)` ✅
- Source:
  - `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip` :contentReference[oaicite:16]{index=16}  
- **Implementation**: `DownloadBulkCompanyfactsZipTool` in `bulk_data_tools.py`

### 8.3 `extract_bulk_zip(zip_path, dest_dir)` ✅
- Unzips into JSON files.
- **Implementation**: `ExtractBulkZipTool` in `bulk_data_tools.py`

> For a single-ticker agent, bulk is optional, but these tools allow offline/fast lookup.

---

## 9) RSS / “Latest Filings” Monitoring Tools

SEC provides RSS feeds including EDGAR search RSS links. :contentReference[oaicite:17]{index=17}  

### 9.1 `get_company_edgar_rss_feed_url(cik_or_query_params)`
- Note: EDGAR searches expose an RSS link for a company’s filings; implement by constructing the EDGAR search URL and locating the RSS link.
- Doc reference: SEC RSS overview & EDGAR search RSS capability. :contentReference[oaicite:18]{index=18}  

### 9.2 `fetch_rss(url)`
- Returns parsed items: title, link, pubDate, description.

### 9.3 `rss_items_to_filings(items)`
- Extract accession / form / cik when possible from RSS links.

---

## 10) Common Higher-Level Convenience Tools (Built from Atomics)

These are “composite” but still useful as first-class tools.

### 10.1 `get_latest_10q_or_10k(ticker)` ✅
- Steps:
  - `ticker_to_cik` → `list_recent_filings(forms=["10-Q","10-K"])` → pick latest.
- **Implementation**: `GetLatest10qOr10kTool` in `convenience_tools.py`

### 10.2 `get_latest_8k(ticker)` ✅
- Same pattern with `forms=["8-K"]`
- **Implementation**: `GetLatest8kTool` in `convenience_tools.py`

### 10.3 `get_filing_docs_bundle(ticker, form)` ✅
- Returns:
  - `FilingMeta`
  - parsed doc index list
  - URLs for primary docs + exhibits
  - optional downloaded local paths
- **Implementation**: `GetFilingDocsBundleTool` in `convenience_tools.py`

### 10.4 `get_key_financial_series(ticker, tags=[...])` ✅
- Uses:
  - `get_company_facts` or `get_company_concept` per tag
- Returns:
  - normalized series aligned by period.
- **Implementation**: `GetKeyFinancialSeriesTool` in `convenience_tools.py`

---

## 11) Implementation Notes (Non-negotiable)

### Headers
- Always set `User-Agent` and honor rate limits. :contentReference[oaicite:19]{index=19}  

### Prefer structured XBRL facts when you can
- Company facts and concept APIs exist specifically to provide JSON-formatted extracted XBRL data. :contentReference[oaicite:20]{index=20}  

### Fallbacks
- If XBRL facts are missing for a given tag or filing:
  - use the filing index to locate HTML/TXT statement exhibits and parse tables as a fallback (still from the SEC source).

---

## 12) Source Documentation Links (for implementer reference)

- EDGAR Application Programming Interfaces (submissions + XBRL data APIs):  
  https://www.sec.gov/search-filings/edgar-application-programming-interfaces :contentReference[oaicite:21]{index=21}  
- Accessing EDGAR Data (fair access / headers / rate limits):  
  https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data :contentReference[oaicite:22]{index=22}  
- data.sec.gov landing (points to API docs + fair access resources):  
  https://data.sec.gov/ :contentReference[oaicite:23]{index=23}  
- EDGAR daily indexes directory:  
  https://www.sec.gov/Archives/edgar/daily-index/ :contentReference[oaicite:24]{index=24}  
- EDGAR full indexes directory:  
  https://www.sec.gov/Archives/edgar/full-index/ :contentReference[oaicite:25]{index=25}  
- SEC RSS Feeds (EDGAR search RSS guidance):  
  https://www.sec.gov/about/rss-feeds :contentReference[oaicite:26]{index=26}  

