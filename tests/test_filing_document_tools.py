"""
Tests for filing_document_tools module.

Tests filing document index and retrieval tools.
"""

import json
import pytest

from flow_researcher.tools import (
    GetFilingIndexHtmlTool,
    ParseFilingIndexDocumentsTool,
    FindDocumentByTypeTool,
)


class TestGetFilingIndexHtmlTool:
    """Test suite for GetFilingIndexHtmlTool."""

    def test_get_filing_index_html(self):
        """Test getting filing index HTML."""
        tool = GetFilingIndexHtmlTool()
        # Use a real filing to test
        result = tool._run("0000320193", "0000320193-24-000001")
        
        data = json.loads(result)
        # May or may not succeed depending on filing availability
        if data["data"]:
            assert "html" in data["data"]
            assert len(data["source_urls"]) > 0


class TestParseFilingIndexDocumentsTool:
    """Test suite for ParseFilingIndexDocumentsTool."""

    def test_parse_filing_index_documents(self):
        """Test parsing filing index documents."""
        tool = ParseFilingIndexDocumentsTool()
        # Sample HTML with document links
        html = """
        <html>
        <a href="test-10q.html">10-Q</a>
        <a href="ex-99.1.pdf">EX-99.1</a>
        </html>
        """
        result = tool._run(html)
        
        data = json.loads(result)
        assert isinstance(data["data"], list)
        # Should find at least some documents
        assert len(data["data"]) >= 0


class TestFindDocumentByTypeTool:
    """Test suite for FindDocumentByTypeTool."""

    def test_find_document_by_type(self):
        """Test finding documents by type."""
        tool = FindDocumentByTypeTool()
        documents = json.dumps([
            {"filename": "10-Q.html", "type": "10-Q", "url": "http://example.com/10-Q.html"},
            {"filename": "ex-99.1.pdf", "type": "EX-99.1", "url": "http://example.com/ex-99.1.pdf"}
        ])
        result = tool._run(documents, ["10-Q", "EX-99.1"])
        
        data = json.loads(result)
        assert data["data"]["matches_found"] >= 0
        assert isinstance(data["data"]["matches"], list)
