"""
Tests for convenience_tools module.

Tests higher-level convenience tools that combine multiple tools.
"""

import json
import pytest

from flow_researcher.tools import (
    GetLatest10qOr10kTool,
    GetLatest8kTool,
)


class TestGetLatest10qOr10kTool:
    """Test suite for GetLatest10qOr10kTool."""

    def test_get_latest_10q_or_10k(self):
        """Test getting latest 10-Q or 10-K."""
        tool = GetLatest10qOr10kTool()
        result = tool._run("AAPL")
        
        data = json.loads(result)
        # May or may not have data
        if data["data"]:
            assert "form" in data["data"]
            assert data["data"]["form"] in ["10-Q", "10-K"]
            assert len(data["source_urls"]) > 0


class TestGetLatest8kTool:
    """Test suite for GetLatest8kTool."""

    def test_get_latest_8k(self):
        """Test getting latest 8-K."""
        tool = GetLatest8kTool()
        result = tool._run("AAPL")
        
        data = json.loads(result)
        # May or may not have data
        if data["data"]:
            assert data["data"]["form"] == "8-K"
            assert len(data["source_urls"]) > 0
