#!/usr/bin/env python
"""Main entry point for flow_researcher."""

from flow_researcher.flows.financial_snapshot_flow import FinancialSnapshotFlow, FinancialSnapshotState


def kickoff():
    """Run the default flow (financial snapshot flow)."""
    import os
    # Get ticker from environment variable or use default
    ticker = os.getenv("TICKER", "LAD")
    financial_snapshot(ticker)


def financial_snapshot(ticker: str = "LAD"):
    """
    Run the financial snapshot flow for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
    
    Returns:
        The flow result
    """
    flow = FinancialSnapshotFlow()
    # Pass ticker directly as a parameter (Enterprise will discover this)
    result = flow.kickoff({"ticker": ticker})
    
    # Print the summary
    print("\n" + "="*60)
    print("FINANCIAL SNAPSHOT SUMMARY")
    print("="*60)
    if flow.state.snapshot_summary:
        print(flow.state.snapshot_summary)
    else:
        print(f"Ticker: {flow.state.ticker}")
        print(f"CIK: {flow.state.cik}")
        if flow.state.error_message:
            print(f"Error: {flow.state.error_message}")
    print("="*60)
    
    return result


def plot():
    """Plot the financial snapshot flow."""
    flow = FinancialSnapshotFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    import json
    import sys

    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Create flow and kickoff with trigger payload
    # The @start() methods will automatically receive crewai_trigger_payload parameter
    flow = FinancialSnapshotFlow()

    try:
        result = flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    # Run financial snapshot flow
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "LAD"
    financial_snapshot(ticker)
