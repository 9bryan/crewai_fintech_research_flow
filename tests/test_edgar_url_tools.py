"""
Tests for edgar_url_tools module.

Tests EDGAR archive URL construction tools.
"""

import json
import pytest

from flow_researcher.tools import (
    AccessionToNodashesTool,
    BuildFilingIndexUrlTool,
    BuildCompleteSubmissionTxtUrlTool,
    BuildFilingFolderUrlTool,
)


class TestAccessionToNodashesTool:
    """Test suite for AccessionToNodashesTool."""

    def test_accession_to_nodashes(self):
        """Test converting accession number format."""
        tool = AccessionToNodashesTool()
        result = tool._run("0000320193-25-000010")
        
        data = json.loads(result)
        assert data["data"]["accession_no_dashes"] == "000032019325000010"
        assert data["warnings"] == []


class TestBuildFilingIndexUrlTool:
    """Test suite for BuildFilingIndexUrlTool."""

    def test_build_filing_index_url(self):
        """Test building filing index URL."""
        tool = BuildFilingIndexUrlTool()
        result = tool._run("0000320193", "0000320193-25-000010")
        
        data = json.loads(result)
        assert "index.html" in data["data"]["url"]
        assert "0000320193" in data["data"]["url"]
        assert data["data"]["cik"] == "0000320193"


class TestBuildCompleteSubmissionTxtUrlTool:
    """Test suite for BuildCompleteSubmissionTxtUrlTool."""

    def test_build_complete_submission_txt_url(self):
        """Test building complete submission text URL."""
        tool = BuildCompleteSubmissionTxtUrlTool()
        result = tool._run("0000320193", "0000320193-25-000010")
        
        data = json.loads(result)
        assert data["data"]["url"].endswith(".txt")
        assert "0000320193" in data["data"]["url"]


class TestBuildFilingFolderUrlTool:
    """Test suite for BuildFilingFolderUrlTool."""

    def test_build_filing_folder_url(self):
        """Test building filing folder URL."""
        tool = BuildFilingFolderUrlTool()
        result = tool._run("0000320193", "0000320193-25-000010")
        
        data = json.loads(result)
        assert data["data"]["url"].endswith("/")
        assert "000032019325000010" in data["data"]["url"]  # No dashes
        assert data["data"]["accession_no_dashes"] == "000032019325000010"
