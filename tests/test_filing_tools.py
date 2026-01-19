"""
Tests for filing_tools module.

Tests filing discovery and metadata tools.
"""

import json
import pytest

from flow_researcher.tools import (
    ListRecentFilingsTool,
    GetLatestFilingTool,
    GetFilingsByDateRangeTool,
    GetFilingAcceptanceDatetimeTool,
)


class TestListRecentFilingsTool:
    """Test suite for ListRecentFilingsTool."""

    def test_list_all_filings(self):
        """Test listing recent filings without filters."""
        tool = ListRecentFilingsTool()
        result = tool._run("0000320193", forms=None, limit=5)
        
        data = json.loads(result)
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 5
        if data["data"]:
            assert "form" in data["data"][0]
            assert "accessionNumber" in data["data"][0]

    def test_list_filtered_filings(self):
        """Test listing filings filtered by form type."""
        tool = ListRecentFilingsTool()
        result = tool._run("0000320193", forms=["10-Q"], limit=3)
        
        data = json.loads(result)
        assert isinstance(data["data"], list)
        # All returned filings should be 10-Q
        for filing in data["data"]:
            assert filing["form"] == "10-Q"


class TestGetLatestFilingTool:
    """Test suite for GetLatestFilingTool."""

    def test_get_latest_10q(self):
        """Test getting latest 10-Q filing."""
        tool = GetLatestFilingTool()
        result = tool._run("0000320193", "10-Q")
        
        data = json.loads(result)
        if data["data"]:  # May not have 10-Q if company doesn't file it
            assert data["data"]["form"] == "10-Q"
            assert "accessionNumber" in data["data"]
            assert "filingDate" in data["data"]


class TestGetFilingsByDateRangeTool:
    """Test suite for GetFilingsByDateRangeTool."""

    def test_get_filings_in_range(self):
        """Test getting filings within a date range."""
        tool = GetFilingsByDateRangeTool()
        result = tool._run("0000320193", "2024-01-01", "2024-12-31", forms=["10-Q"])
        
        data = json.loads(result)
        assert isinstance(data["data"], list)
        # Verify dates are in range
        for filing in data["data"]:
            if filing.get("filingDate"):
                filing_date = filing["filingDate"]
                assert "2024" in filing_date

    def test_invalid_date_range(self):
        """Test with invalid date range (start > end)."""
        tool = GetFilingsByDateRangeTool()
        result = tool._run("0000320193", "2024-12-31", "2024-01-01", forms=None)
        
        data = json.loads(result)
        assert data["data"] == []
        assert len(data["warnings"]) > 0
        assert "before" in data["warnings"][0].lower() or "after" in data["warnings"][0].lower()


class TestGetFilingAcceptanceDatetimeTool:
    """Test suite for GetFilingAcceptanceDatetimeTool."""

    def test_extract_acceptance_datetime(self):
        """Test extracting acceptance datetime from filing metadata."""
        # First get a filing with acceptance datetime
        filings_tool = GetLatestFilingTool()
        filing_result = filings_tool._run("0000320193", "10-Q")
        
        filing_data = json.loads(filing_result)
        if filing_data.get("data") and filing_data["data"].get("acceptanceDateTime"):
            tool = GetFilingAcceptanceDatetimeTool()
            filing_meta = json.dumps(filing_data["data"])
            result = tool._run(filing_meta)
            
            result_data = json.loads(result)
            assert result_data["data"] is not None
            assert "acceptanceDateTime" in result_data["data"]
        else:
            pytest.skip("No filing with acceptanceDateTime available for testing")

    def test_missing_acceptance_datetime(self):
        """Test with filing metadata that lacks acceptance datetime."""
        tool = GetFilingAcceptanceDatetimeTool()
        filing_meta = json.dumps({"form": "10-Q", "filingDate": "2024-01-01"})
        result = tool._run(filing_meta)
        
        data = json.loads(result)
        assert data["data"] is None
        assert len(data["warnings"]) > 0
        assert "not available" in data["warnings"][0].lower()
