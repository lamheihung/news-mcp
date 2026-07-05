# Task 008: Testing - Integration Smoke Test

## Description
Run an end-to-end smoke test that starts the MCP server and invokes each tool through the transport.

## Requirements
- Start the server with `uv run main.py` or a FastMCP test client.
- Call `list_sources` and verify the response matches `config.yaml`.
- Call `resolve_company` with a known identifier and verify a `Company` is returned.
- Call `research_company` and verify a list of `Article` objects is returned.
- Ensure the test exits cleanly and terminates the server process if running in a subprocess.

## Dependencies
- Blocks: []
- Blocked by: [003, 005, 006]
- Parallelizable with: [007]

## Success Criteria (5 points)
1. The server process starts and responds to an initialization request within five seconds.
2. The `list_sources` tool call returns the sources configured in `config.yaml`.
3. The `resolve_company` tool call returns a `Company` with a non-empty `bloomberg_ticker`.
4. The `research_company` tool call returns at least one `Article` with all required fields populated.
5. The test suite exits cleanly and terminates the server process.

## Status
[008-testing-integration-smoke-status.md](../status/008-testing-integration-smoke-status.md)
