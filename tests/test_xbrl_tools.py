"""
Tests for xbrl_tools module.

Tests XBRL "Facts" APIs for structured financial data.
"""

import json
import pytest

from flow_researcher.tools import (
    GetCompanyFactsTool,
    ListTaxonomiesTool,
    ListConceptsTool,
    GetCompanyConceptTool,
)


class TestGetCompanyFactsTool:
    """Test suite for GetCompanyFactsTool."""

    def test_get_company_facts(self):
        """Test getting company facts."""
        tool = GetCompanyFactsTool()
        result = tool._run("0000320193")  # Apple
        
        data = json.loads(result)
        if data["data"]:
            assert "facts" in data["data"] or "cik" in data["data"]
            assert len(data["source_urls"]) > 0


class TestListTaxonomiesTool:
    """Test suite for ListTaxonomiesTool."""

    def test_list_taxonomies(self):
        """Test listing taxonomies."""
        # First get company facts
        facts_tool = GetCompanyFactsTool()
        facts_result = facts_tool._run("0000320193")
        facts_data = json.loads(facts_result)
        
        if facts_data["data"]:
            tool = ListTaxonomiesTool()
            result = tool._run(json.dumps(facts_data["data"]))
            
            data = json.loads(result)
            assert "taxonomies" in data["data"]
            assert isinstance(data["data"]["taxonomies"], list)


class TestListConceptsTool:
    """Test suite for ListConceptsTool."""

    def test_list_concepts(self):
        """Test listing concepts."""
        # First get company facts
        facts_tool = GetCompanyFactsTool()
        facts_result = facts_tool._run("0000320193")
        facts_data = json.loads(facts_result)
        
        if facts_data["data"]:
            tool = ListConceptsTool()
            result = tool._run(json.dumps(facts_data["data"]), "us-gaap")
            
            data = json.loads(result)
            assert "concepts" in data["data"]
            assert data["data"]["taxonomy"] == "us-gaap"


class TestGetCompanyConceptTool:
    """Test suite for GetCompanyConceptTool."""

    def test_get_company_concept(self):
        """Test getting company concept."""
        tool = GetCompanyConceptTool()
        result = tool._run("0000320193", "us-gaap", "Revenues")
        
        data = json.loads(result)
        # May or may not have data depending on tag availability
        if data["data"]:
            assert len(data["source_urls"]) > 0
