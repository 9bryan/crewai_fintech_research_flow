"""
Tests for edgar_index_tools module.

Tests EDGAR index files (daily/quarterly/full) tools.
"""

import json
import pytest

from flow_researcher.tools import (
    ListDailyIndexPathsTool,
    EdgarPathToDocUrlTool,
)


class TestListDailyIndexPathsTool:
    """Test suite for ListDailyIndexPathsTool."""

    def test_list_daily_index_paths(self):
        """Test listing daily index paths."""
        tool = ListDailyIndexPathsTool()
        result = tool._run(2024, 1)
        
        data = json.loads(result)
        assert data["data"]["year"] == 2024
        assert data["data"]["quarter"] == 1
        assert len(data["data"]["paths"]) > 0


class TestEdgarPathToDocUrlTool:
    """Test suite for EdgarPathToDocUrlTool."""

    def test_edgar_path_to_doc_url(self):
        """Test converting EDGAR path to URL."""
        tool = EdgarPathToDocUrlTool()
        result = tool._run("edgar/data/320193/000032019325000010/test.html")
        
        data = json.loads(result)
        assert "sec.gov" in data["data"]["url"]
        assert "Archives" in data["data"]["url"]
