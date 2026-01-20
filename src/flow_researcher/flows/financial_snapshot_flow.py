"""
Company Financial Snapshot Flow.

A simple flow that retrieves a company's financial overview including:
- Company profile information
- Key financial metrics (Revenues, Net Income, Assets)
"""

import json
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any

from crewai.flow import Flow, listen, router, start

from flow_researcher.tools import (
    TickerToCikTool,
    GetCompanyProfileTool,
    GetKeyFinancialSeriesTool,
)
from flow_researcher.crews.financial_analyst_crew.financial_analyst_crew import FinancialAnalystCrew


class FinancialSnapshotState(BaseModel):
    """State for the financial snapshot flow.
    
    Note: Only 'ticker' should be provided as input. All other fields are
    populated internally by the flow and should not be set via inputs.
    """
    ticker: str = Field(default="LAD", description="Stock ticker symbol")
    cik: str = Field(default="", description="Company CIK number")
    company_profile: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    financial_metrics: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    snapshot_summary: str = Field(default="", description="Formatted summary of the snapshot")
    error_message: str = Field(default="", description="Error message if any step fails")
    
    model_config = {
        "extra": "forbid",  # Don't allow extra fields
    }
    
    @model_validator(mode="before")
    @classmethod
    def filter_inputs(cls, data):
        """Only allow 'ticker' to be set from external inputs.
        
        Enterprise may try to pass company_profile and financial_metrics,
        but these should be ignored and set internally by the flow.
        """
        if isinstance(data, dict):
            # Only allow ticker from external inputs
            # Ignore company_profile, financial_metrics, cik, etc. - they're internal
            allowed_inputs = {"ticker"}
            filtered = {k: v for k, v in data.items() if k in allowed_inputs}
            return filtered
        return data


class FinancialSnapshotFlow(Flow[FinancialSnapshotState]):
    """Flow to generate a company financial snapshot."""

    @start()
    def initialize_ticker(self, ticker: str = "LAD", crewai_trigger_payload: dict = None):
        """
        Initialize the flow with a ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "MSFT"). Defaults to "LAD".
            crewai_trigger_payload: Optional trigger payload (for backward compatibility).
        
        Can receive ticker as a direct parameter or from trigger payload.
        """
        # Priority: direct parameter > trigger payload > default
        if ticker and ticker != "LAD":  # Explicit ticker provided
            self.state.ticker = ticker.upper().strip()
            print(f"[FinancialSnapshotFlow]: Received ticker parameter: {self.state.ticker}")
        elif crewai_trigger_payload and crewai_trigger_payload.get("ticker"):
            self.state.ticker = crewai_trigger_payload.get("ticker", "").upper().strip()
            print(f"[FinancialSnapshotFlow]: Received ticker from trigger: {self.state.ticker}")
        else:
            # Default ticker
            self.state.ticker = "LAD"
            print(f"[FinancialSnapshotFlow]: Using default ticker: {self.state.ticker}")
        
        if not self.state.ticker:
            self.state.error_message = "No ticker provided"
            return "error"
        
        return "ticker_initialized"

    @listen(initialize_ticker)
    def get_company_info(self):
        """
        Convert ticker to CIK and get company profile.
        
        Uses TickerToCikTool and GetCompanyProfileTool.
        """
        print(f"[FinancialSnapshotFlow]: Getting company information for {self.state.ticker}")
        
        try:
            # Convert ticker to CIK
            ticker_tool = TickerToCikTool()
            cik_result = ticker_tool._run(self.state.ticker)
            cik_data = json.loads(cik_result)
            
            if not cik_data.get("data"):
                self.state.error_message = cik_data.get("warnings", ["Ticker not found"])[0]
                return "company_not_found"
            
            self.state.cik = cik_data["data"]["cik"]
            print(f"[FinancialSnapshotFlow]: Found CIK: {self.state.cik}")
            
            # Get company profile
            profile_tool = GetCompanyProfileTool()
            profile_result = profile_tool._run(self.state.ticker)
            profile_data = json.loads(profile_result)
            
            if profile_data.get("data"):
                self.state.company_profile = profile_data["data"]
                print(f"[FinancialSnapshotFlow]: Retrieved company profile")
                return "company_found"
            else:
                self.state.error_message = "Failed to retrieve company profile"
                return "company_not_found"
                
        except Exception as e:
            self.state.error_message = f"Error getting company info: {str(e)}"
            return "error"

    @router(get_company_info)
    def route_by_company_status(self, status: str):
        """
        Route based on whether company was found.
        
        Returns 'fetch_metrics' if company found, 'handle_error' otherwise.
        """
        if status == "company_found":
            print(f"[FinancialSnapshotFlow]: Company found, proceeding to fetch financial metrics")
            return "fetch_metrics"
        else:
            print(f"[FinancialSnapshotFlow]: Company not found or error occurred")
            return "handle_error"

    @listen("fetch_metrics")
    def get_financial_metrics(self):
        """
        Get key financial metrics for the company.
        
        Retrieves Revenues, Net Income, and Assets using GetKeyFinancialSeriesTool.
        """
        print(f"[FinancialSnapshotFlow]: Fetching financial metrics for {self.state.ticker}")
        
        try:
            metrics_tool = GetKeyFinancialSeriesTool()
            result = metrics_tool._run(
                self.state.ticker,
                ["Revenues", "NetIncomeLoss", "Assets"]
            )
            
            metrics_data = json.loads(result)
            
            if metrics_data.get("data") and metrics_data["data"].get("series"):
                self.state.financial_metrics = metrics_data["data"]
                print(f"[FinancialSnapshotFlow]: Retrieved financial metrics")
            else:
                self.state.error_message = "No financial metrics available"
                print(f"[FinancialSnapshotFlow]: Warning - No financial metrics available")
            
            return "metrics_fetched"
                
        except Exception as e:
            self.state.error_message = f"Error fetching metrics: {str(e)}"
            return "metrics_fetched"  # Continue even if metrics fail

    @listen("metrics_fetched")
    def generate_snapshot_summary(self):
        """
        Generate a formatted summary of the financial snapshot.
        
        Uses the FinancialAnalystCrew to analyze the data and create a comprehensive summary.
        """
        print(f"[FinancialSnapshotFlow]: Generating snapshot summary using FinancialAnalystCrew")
        
        try:
            # Prepare inputs for the crew
            profile_info = json.dumps(self.state.company_profile, indent=2) if self.state.company_profile else "N/A"
            metrics_info = json.dumps(self.state.financial_metrics, indent=2) if self.state.financial_metrics else "N/A"
            
            crew_inputs = {
                "ticker": self.state.ticker,
                "cik": self.state.cik,
                "company_profile": profile_info,
                "financial_metrics": metrics_info,
            }
            
            # Run the financial analyst crew
            result = (
                FinancialAnalystCrew()
                .crew()
                .kickoff(inputs=crew_inputs)
            )
            
            # Extract the summary from the crew result
            # The final task (synthesize_financial_snapshot) should contain the summary
            # CrewAI results typically have .raw for the raw output or we can access task outputs
            if hasattr(result, 'raw') and result.raw:
                self.state.snapshot_summary = str(result.raw)
            elif hasattr(result, 'tasks_output') and result.tasks_output:
                # Get output from the last task (synthesize_financial_snapshot)
                if isinstance(result.tasks_output, list) and len(result.tasks_output) > 0:
                    self.state.snapshot_summary = str(result.tasks_output[-1])
                elif result.tasks_output:
                    self.state.snapshot_summary = str(result.tasks_output)
            else:
                # Fallback: try to get any available output
                self.state.snapshot_summary = str(result) if result else "Analysis completed but no summary generated."
            
            print(f"[FinancialSnapshotFlow]: Summary generated by crew")
            return "summary_complete"
            
        except Exception as e:
            self.state.error_message = f"Error generating summary: {str(e)}"
            self.state.snapshot_summary = f"Error: {self.state.error_message}"
            return "summary_complete"

    @listen("handle_error")
    def handle_error(self):
        """
        Handle errors and generate error message.
        """
        print(f"[FinancialSnapshotFlow]: Error occurred: {self.state.error_message}")
        if not self.state.snapshot_summary:
            self.state.snapshot_summary = f"Error: {self.state.error_message}"
        return "flow_complete"

    @listen("summary_complete")
    def complete_flow(self):
        """
        Mark flow as complete.
        """
        print(f"[FinancialSnapshotFlow]: Flow completed successfully")
        return "flow_complete"
