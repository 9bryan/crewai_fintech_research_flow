"""
Tests for company_tools module.

Tests company identity and lookup tools.
"""

import json
import pytest

from flow_researcher.tools import (
    GetTickerCikMapTool,
    TickerToCikTool,
    GetCompanySubmissionsTool,
    GetCompanyProfileTool,
)


class TestTickerToCikTool:
    """Test suite for TickerToCikTool."""

    def test_basic_conversion(self):
        """Test converting a ticker to CIK."""
        tool = TickerToCikTool()
        result = tool._run("AAPL")
        
        data = json.loads(result)
        assert data["data"] is not None
        assert data["data"]["cik"] == "0000320193"
        assert data["data"]["ticker"] == "AAPL"
        assert len(data["source_urls"]) > 0
        assert data["warnings"] == []

    def test_invalid_ticker(self):
        """Test with a ticker that doesn't exist."""
        tool = TickerToCikTool()
        result = tool._run("INVALIDTICKER123")
        
        data = json.loads(result)
        assert data["data"] is None
        assert len(data["warnings"]) > 0
        assert "not found" in data["warnings"][0].lower()


class TestGetTickerCikMapTool:
    """Test suite for GetTickerCikMapTool."""

    def test_get_map(self):
        """Test getting the ticker CIK map."""
        tool = GetTickerCikMapTool()
        result = tool._run()
        
        data = json.loads(result)
        assert data["data"] is not None
        assert len(data["source_urls"]) > 0
        # Should have some data structure (dict or list)
        assert isinstance(data["data"], (dict, list))


class TestGetCompanySubmissionsTool:
    """Test suite for GetCompanySubmissionsTool."""

    def test_get_submissions(self):
        """Test getting company submissions."""
        tool = GetCompanySubmissionsTool()
        result = tool._run("0000320193")  # Apple's CIK
        
        data = json.loads(result)
        assert data["data"] is not None
        assert "filings" in data["data"] or "name" in data["data"]
        assert len(data["source_urls"]) > 0


class TestGetCompanyProfileTool:
    """Test suite for GetCompanyProfileTool."""

    def test_get_profile(self):
        """Test getting company profile."""
        tool = GetCompanyProfileTool()
        result = tool._run("AAPL")
        
        data = json.loads(result)
        assert data["data"] is not None
        assert data["data"]["cik"] == "0000320193"
        assert data["data"]["ticker"] == "AAPL"
        assert "entity_name" in data["data"]
        assert len(data["source_urls"]) > 0
