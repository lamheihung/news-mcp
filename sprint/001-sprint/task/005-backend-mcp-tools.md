# Task 005: Backend - MCP Tools

## Description
Implement the three MCP tool handlers: `list_sources`, `resolve_company`, and `research_company`.

## Requirements
- Implement all tool handlers in `src/tools.py`.
- `list_sources` returns the sources loaded from `config.yaml`.
- `resolve_company` wraps the resolver and returns a `Company`.
- `research_company` accepts `bloomberg_ticker`, `question`, optional `start_date`, optional `end_date`, and optional `sources`, then returns sample/mock `Article` objects.
- Convert ISO date strings to a `DateRange` with a default lookback of six months and filter mock articles by requested source IDs when provided.

## Dependencies
- Blocks: [006, 007, 008]
- Blocked by: [001, 002, 004]
- Parallelizable with: [003]

## Success Criteria (5 points)
1. `list_sources()` returns the exact list of `Source` models loaded from `config.yaml`.
2. `resolve_company("Microsoft")` returns a `Company` via the registered tool handler.
3. `research_company` called without dates returns mock articles dated within the last six months.
4. `research_company` with a `sources` filter only returns articles whose `source_id` is in the requested list.
5. All three handlers are decorated as FastMCP tools and have type annotations matching the architecture.

## Status
[005-backend-mcp-tools-status.md](../status/005-backend-mcp-tools-status.md)
