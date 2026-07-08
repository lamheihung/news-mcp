# Task 015: Testing - Integration Updates

## Description
Update the integration smoke test to account for the new `pcwatch` source and optional real scraping path.

## Requirements
- Verify `list_sources` returns both `example` and `pcwatch` sources.
- Keep the existing `example` source smoke test path.
- Optionally exercise `research_company` with `pcwatch` when Playwright and a browser are available, skipping otherwise.
- Skip the live resolver call gracefully when `GEMINI_API_KEY` is missing or the API fails.
- Ensure the server starts over stdio and registers all three tools.

## Dependencies
- Blocks: None
- Blocked by: [007, 010]
- Parallelizable with: [013, 014]

## Success Criteria (5 points)
1. Integration test verifies `pcwatch` is present in configured sources.
2. `research_company` smoke test includes `pcwatch` when browser automation is available.
3. Test skips gracefully when `GEMINI_API_KEY` or Playwright/browser is unavailable.
4. End-to-end stdio server starts and registers the three MCP tools.
5. Test completes within 60 seconds.

## Status
[015-testing-integration-updates-status.md](../status/015-testing-integration-updates-status.md)
