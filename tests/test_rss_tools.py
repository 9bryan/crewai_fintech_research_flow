"""
Tests for rss_tools module.

Tests RSS / "Latest Filings" monitoring tools.
"""

import json
import pytest

from flow_researcher.tools import (
    GetCompanyEdgarRssFeedUrlTool,
)


class TestGetCompanyEdgarRssFeedUrlTool:
    """Test suite for GetCompanyEdgarRssFeedUrlTool."""

    def test_get_company_edgar_rss_feed_url(self):
        """Test getting company EDGAR RSS feed URL."""
        tool = GetCompanyEdgarRssFeedUrlTool()
        result = tool._run("0000320193")
        
        data = json.loads(result)
        assert "sec.gov" in data["data"]["url"]
        assert "atom" in data["data"]["url"] or "rss" in data["data"]["url"]
        assert data["data"]["cik"] == "0000320193"
