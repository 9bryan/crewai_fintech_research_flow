"""
XBRL "Facts" APIs Tools.

These tools access structured financial data from SEC's XBRL APIs.
"""

import json
from typing import Type, Optional, List, Dict, Any

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from .sec_http_client import get_default_client


class GetCompanyFactsInput(BaseModel):
    """Input schema for get_company_facts tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")


class GetCompanyFactsTool(BaseTool):
    """
    Get company facts (XBRL data).
    
    Retrieves the complete company facts JSON which contains all XBRL
    financial data for a company across all taxonomies.
    """
    name: str = "get_company_facts"
    description: str = """
    Retrieves the complete company facts JSON from SEC's XBRL API. This contains
    all structured financial data for a company across all taxonomies (us-gaap,
    dei, ifrs-full, etc.). This is the primary source for structured financial data.
    """
    args_schema: Type[BaseModel] = GetCompanyFactsInput

    def _run(self, cik: str) -> str:
        cik_padded = cik.strip().zfill(10)
        client = get_default_client()
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
        
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
                "warnings": [f"Failed to fetch company facts: {str(e)}"]
            })


class ListTaxonomiesInput(BaseModel):
    """Input schema for list_taxonomies tool."""
    companyfacts_json: str = Field(
        ...,
        description="JSON string from get_company_facts tool"
    )


class ListTaxonomiesTool(BaseTool):
    """
    List available taxonomies in company facts.
    
    Extracts the list of available taxonomies (e.g., us-gaap, dei, ifrs-full, srt)
    from company facts data.
    """
    name: str = "list_taxonomies"
    description: str = """
    Lists all available taxonomies in company facts data. Common taxonomies include:
    us-gaap (US Generally Accepted Accounting Principles), dei (Document and Entity
    Information), ifrs-full (International Financial Reporting Standards), srt, etc.
    """
    args_schema: Type[BaseModel] = ListTaxonomiesInput

    def _run(self, companyfacts_json: str) -> str:
        try:
            if isinstance(companyfacts_json, str):
                facts = json.loads(companyfacts_json)
            else:
                facts = companyfacts_json
            
            # Extract taxonomies from facts structure
            # Structure: facts["facts"] contains taxonomy keys
            if isinstance(facts, dict) and "facts" in facts:
                taxonomies = list(facts["facts"].keys())
            elif isinstance(facts, dict) and "data" in facts and isinstance(facts["data"], dict) and "facts" in facts["data"]:
                taxonomies = list(facts["data"]["facts"].keys())
            else:
                # Try to find any dict keys that look like taxonomies
                taxonomies = [k for k in facts.keys() if isinstance(facts.get(k), dict)]
            
            result = {
                "data": {
                    "taxonomies": taxonomies,
                    "count": len(taxonomies)
                },
                "source_urls": [],
                "warnings": [] if taxonomies else ["No taxonomies found in company facts"]
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": {"taxonomies": [], "count": 0},
                "source_urls": [],
                "warnings": ["Invalid JSON in companyfacts_json parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": {"taxonomies": [], "count": 0},
                "source_urls": [],
                "warnings": [f"Failed to list taxonomies: {str(e)}"]
            })


class ListConceptsInput(BaseModel):
    """Input schema for list_concepts tool."""
    companyfacts_json: str = Field(
        ...,
        description="JSON string from get_company_facts tool"
    )
    taxonomy: str = Field(
        default="us-gaap",
        description="Taxonomy name (e.g., 'us-gaap', 'dei', 'ifrs-full')"
    )


class ListConceptsTool(BaseTool):
    """
    List available concepts/tags in a taxonomy.
    
    Extracts the list of available XBRL concepts (tags) for a company
    within a specific taxonomy.
    """
    name: str = "list_concepts"
    description: str = """
    Lists all available XBRL concepts (tags) for a company within a specific
    taxonomy. Concepts are the standardized tags used to represent financial
    data (e.g., 'Revenues', 'Assets', 'NetIncomeLoss').
    """
    args_schema: Type[BaseModel] = ListConceptsInput

    def _run(self, companyfacts_json: str, taxonomy: str = "us-gaap") -> str:
        try:
            if isinstance(companyfacts_json, str):
                facts = json.loads(companyfacts_json)
            else:
                facts = companyfacts_json
            
            # Extract concepts from facts structure
            concepts = []
            if isinstance(facts, dict):
                # Handle different possible structures
                facts_data = facts.get("facts") or facts.get("data", {}).get("facts", {})
                if taxonomy in facts_data:
                    concepts = list(facts_data[taxonomy].keys())
            
            result = {
                "data": {
                    "taxonomy": taxonomy,
                    "concepts": concepts,
                    "count": len(concepts)
                },
                "source_urls": [],
                "warnings": [] if concepts else [f"No concepts found for taxonomy '{taxonomy}'"]
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": {"taxonomy": taxonomy, "concepts": [], "count": 0},
                "source_urls": [],
                "warnings": ["Invalid JSON in companyfacts_json parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": {"taxonomy": taxonomy, "concepts": [], "count": 0},
                "source_urls": [],
                "warnings": [f"Failed to list concepts: {str(e)}"]
            })


class GetCompanyConceptInput(BaseModel):
    """Input schema for get_company_concept tool."""
    cik: str = Field(..., description="10-digit zero-padded CIK number")
    taxonomy: str = Field(
        default="us-gaap",
        description="Taxonomy name (e.g., 'us-gaap', 'dei')"
    )
    tag: str = Field(..., description="Concept tag (e.g., 'Revenues', 'Assets')")


class GetCompanyConceptTool(BaseTool):
    """
    Get company concept (time-series data for a tag).
    
    Retrieves time-series fact data for a single XBRL concept/tag,
    showing all reported values over time.
    """
    name: str = "get_company_concept"
    description: str = """
    Retrieves time-series data for a single XBRL concept/tag. Returns all
    reported values for that concept over time, including fiscal year, fiscal
    period, end date, value, unit, and filing information. Example: get all
    reported 'Revenues' values for a company.
    """
    args_schema: Type[BaseModel] = GetCompanyConceptInput

    def _run(self, cik: str, taxonomy: str, tag: str) -> str:
        cik_padded = cik.strip().zfill(10)
        client = get_default_client()
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json"
        
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
                "warnings": [f"Failed to fetch company concept: {str(e)}"]
            })


class GetFramesInput(BaseModel):
    """Input schema for get_frames tool."""
    taxonomy: str = Field(
        default="us-gaap",
        description="Taxonomy name (e.g., 'us-gaap')"
    )
    tag: str = Field(..., description="Concept tag (e.g., 'Revenues')")
    unit: str = Field(..., description="Unit (e.g., 'USD', 'shares')")
    period: str = Field(..., description="Period (e.g., 'CY2023', 'CY2023Q1')")


class GetFramesTool(BaseTool):
    """
    Get frames (cross-company data).
    
    Retrieves a cross-company frame showing the same concept across multiple
    companies for a given period. Useful for peer comparisons.
    """
    name: str = "get_frames"
    description: str = """
    Retrieves a cross-company frame showing the same XBRL concept across
    multiple companies for a given period. Useful for peer comparisons and
    validation. Example: get 'Revenues' for all companies in CY2023.
    """
    args_schema: Type[BaseModel] = GetFramesInput

    def _run(self, taxonomy: str, tag: str, unit: str, period: str) -> str:
        client = get_default_client()
        url = f"https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json"
        
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
                "warnings": [f"Failed to fetch frames: {str(e)}"]
            })


class NormalizeFactsToTableInput(BaseModel):
    """Input schema for normalize_facts_to_table tool."""
    companyfacts_json: str = Field(
        ...,
        description="JSON string from get_company_facts tool"
    )
    taxonomy: str = Field(
        default="us-gaap",
        description="Taxonomy name (e.g., 'us-gaap')"
    )


class NormalizeFactsToTableTool(BaseTool):
    """
    Normalize facts to tabular format.
    
    Converts company facts JSON into a normalized tabular format with rows
    containing tag, unit, fiscal year, fiscal period, end date, value, form,
    filed date, frame, and accession number.
    """
    name: str = "normalize_facts_to_table"
    description: str = """
    Converts company facts JSON into a normalized tabular format. Each row
    contains: tag, unit, fy (fiscal year), fp (fiscal period), end (end date),
    val (value), form (filing form), filed (filing date), frame, accn (accession
    number). The accession number can be used to join back to filings/documents.
    """
    args_schema: Type[BaseModel] = NormalizeFactsToTableInput

    def _run(self, companyfacts_json: str, taxonomy: str = "us-gaap") -> str:
        try:
            if isinstance(companyfacts_json, str):
                facts = json.loads(companyfacts_json)
            else:
                facts = companyfacts_json
            
            # Extract facts data
            facts_data = facts.get("facts") or facts.get("data", {}).get("facts", {})
            taxonomy_data = facts_data.get(taxonomy, {})
            
            rows = []
            for tag, tag_data in taxonomy_data.items():
                units = tag_data.get("units", {})
                for unit, unit_data in units.items():
                    for fact in unit_data:
                        row = {
                            "tag": tag,
                            "unit": unit,
                            "fy": fact.get("fy"),
                            "fp": fact.get("fp"),
                            "end": fact.get("end"),
                            "val": fact.get("val"),
                            "form": fact.get("form"),
                            "filed": fact.get("filed"),
                            "frame": fact.get("frame"),
                            "accn": fact.get("accn")
                        }
                        rows.append(row)
            
            result = {
                "data": {
                    "rows": rows,
                    "count": len(rows),
                    "taxonomy": taxonomy
                },
                "source_urls": [],
                "warnings": [] if rows else [f"No facts found for taxonomy '{taxonomy}'"]
            }
            
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps({
                "data": {"rows": [], "count": 0, "taxonomy": taxonomy},
                "source_urls": [],
                "warnings": ["Invalid JSON in companyfacts_json parameter"]
            })
        except Exception as e:
            return json.dumps({
                "data": {"rows": [], "count": 0, "taxonomy": taxonomy},
                "source_urls": [],
                "warnings": [f"Failed to normalize facts: {str(e)}"]
            })


class FactsFilterInput(BaseModel):
    """Input schema for facts_filter tool."""
    rows: str = Field(
        ...,
        description="JSON string of normalized facts rows from normalize_facts_to_table"
    )
    tag: Optional[str] = Field(default=None, description="Filter by tag")
    fp: Optional[str] = Field(default=None, description="Filter by fiscal period (e.g., 'Q1', 'FY')")
    form: Optional[str] = Field(default=None, description="Filter by form type (e.g., '10-Q', '10-K')")
    unit: Optional[str] = Field(default=None, description="Filter by unit (e.g., 'USD')")
    start_end: Optional[str] = Field(default=None, description="Filter by end date (YYYY-MM-DD) or date range (YYYY-MM-DD:YYYY-MM-DD)")


class FactsFilterTool(BaseTool):
    """
    Filter normalized facts rows.
    
    Filters normalized facts rows by various criteria: tag, fiscal period,
    form type, unit, or date range.
    """
    name: str = "facts_filter"
    description: str = """
    Filters normalized facts rows by various criteria. Can filter by:
    - tag: specific XBRL tag/concept
    - fp: fiscal period (Q1, Q2, Q3, Q4, FY)
    - form: filing form type (10-Q, 10-K, etc.)
    - unit: unit of measurement (USD, shares, etc.)
    - start_end: end date or date range (YYYY-MM-DD or YYYY-MM-DD:YYYY-MM-DD)
    """
    args_schema: Type[BaseModel] = FactsFilterInput

    def _run(
        self,
        rows: str,
        tag: Optional[str] = None,
        fp: Optional[str] = None,
        form: Optional[str] = None,
        unit: Optional[str] = None,
        start_end: Optional[str] = None
    ) -> str:
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
            if tag:
                filtered = [r for r in filtered if r.get("tag") == tag]
            if fp:
                filtered = [r for r in filtered if r.get("fp") == fp]
            if form:
                filtered = [r for r in filtered if r.get("form") == form]
            if unit:
                filtered = [r for r in filtered if r.get("unit") == unit]
            if start_end:
                if ":" in start_end:
                    # Date range
                    start, end = start_end.split(":", 1)
                    filtered = [
                        r for r in filtered
                        if r.get("end") and start <= r.get("end") <= end
                    ]
                else:
                    # Single date
                    filtered = [r for r in filtered if r.get("end") == start_end]
            
            result = {
                "data": {
                    "rows": filtered,
                    "count": len(filtered),
                    "original_count": len(rows_list),
                    "filters_applied": {
                        "tag": tag,
                        "fp": fp,
                        "form": form,
                        "unit": unit,
                        "start_end": start_end
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
                "warnings": [f"Failed to filter facts: {str(e)}"]
            })
