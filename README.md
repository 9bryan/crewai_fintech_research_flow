# Flow Researcher

A CrewAI Flow project for financial analysis using SEC data.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment variables:

Create a `.env` file in the root directory with your API keys:

```bash
# For Gemini (Google)
GOOGLE_API_KEY=your_gemini_api_key_here

# Alternative: If you prefer to use GEMINI_API_KEY, you can set both
GEMINI_API_KEY=your_gemini_api_key_here
```

**Note:** LiteLLM (used by CrewAI for Gemini) expects `GOOGLE_API_KEY` by default. If you only have `GEMINI_API_KEY`, you can either:
- Rename it to `GOOGLE_API_KEY` in your `.env` file, or
- Export it: `export GOOGLE_API_KEY=$GEMINI_API_KEY`

## Running the Flow

```bash
# Run with default ticker (LAD)
crewai run

# Or run with a specific ticker using environment variable
TICKER=AAPL crewai run

# Or export it first
export TICKER=MSFT
crewai run
```

## Running Tests

```bash
uv run pytest
```

## Project Structure

- `src/flow_researcher/flows/` - Flow definitions
- `src/flow_researcher/crews/` - Crew definitions
- `src/flow_researcher/tools/` - SEC data tools
- `tests/` - Test files

## Available Models

The project is configured to use Gemini by default. To use a different model, update the `llm` parameter in the crew agents:

```python
llm=LLM(model="gpt-4o")  # OpenAI
llm=LLM(model="anthropic/claude-sonnet-4-20250514")  # Anthropic
llm=LLM(model="gemini/gemini-2.0-flash-exp")  # Gemini (default)
```
