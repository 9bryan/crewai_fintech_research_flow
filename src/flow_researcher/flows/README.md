# Financial Snapshot Flow

A simple CrewAI Flow that demonstrates the use of `@start`, `@listen`, and `@router` decorators to create a company financial snapshot.

## Overview

This flow retrieves a company's financial overview by:
1. Accepting a ticker symbol
2. Converting ticker to CIK and getting company profile
3. Routing based on whether company was found
4. Fetching key financial metrics (Revenues, Net Income, Assets)
5. Generating a formatted summary using the FinancialAnalystCrew

## Flow Structure

```
@start() → initialize_ticker
    ↓
@listen(initialize_ticker) → get_company_info
    ↓
@router(get_company_info) → route_by_company_status
    ├─→ "fetch_metrics" → get_financial_metrics
    │       ↓
    │   @listen("metrics_fetched") → generate_snapshot_summary (calls FinancialAnalystCrew)
    │       ↓
    │   @listen("summary_complete") → complete_flow
    │
    └─→ "handle_error" → handle_error
```

## Usage

### From Python

```python
from flow_researcher.flows.financial_snapshot_flow import FinancialSnapshotFlow

# Create and run the flow
flow = FinancialSnapshotFlow()
result = flow.kickoff({"crewai_trigger_payload": {"ticker": "LAD"}})

# Access the results
print(flow.state.snapshot_summary)
print(flow.state.company_profile)
print(flow.state.financial_metrics)
```

### From Command Line

```bash
# Run with default ticker (LAD)
crewai run

# Run with specific ticker using environment variable
TICKER=AAPL crewai run

# Or run the module directly (accepts ticker as argument)
uv run python -m flow_researcher.main AAPL
```

## Tools Used

- `TickerToCikTool` - Convert ticker to CIK
- `GetCompanyProfileTool` - Get company profile information
- `GetKeyFinancialSeriesTool` - Get financial metrics (Revenues, Net Income, Assets)

## State Model

The flow uses `FinancialSnapshotState` which contains:
- `ticker`: Stock ticker symbol
- `cik`: Company CIK number
- `company_profile`: Company profile data
- `financial_metrics`: Financial metrics data
- `snapshot_summary`: Generated summary text
- `error_message`: Error message if any

## Decorators Demonstrated

- **`@start()`**: Entry point that initializes the ticker
- **`@listen()`**: Listens to previous step completion or router labels
- **`@router()`**: Routes flow based on conditions (company found/not found)

## Example Output

The flow generates a summary like:

```
Apple Inc. (AAPL) is a technology company listed on the Nasdaq exchange...
Recent financial metrics show revenues of $XX billion, net income of $XX billion...
```
