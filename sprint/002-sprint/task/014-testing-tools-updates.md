# Task 014: Testing - Tools Updates

## Description
Update the existing MCP tools tests to cover watchlist updates and scraper orchestration in `research_company`.

## Requirements
- Update `tests/test_tools.py` to verify `resolve_company` upserts the watchlist.
- Verify `research_company` loads scrapers, checks `is_complete`, fetches missing articles, and merges results.
- Add tests for source filtering that include the `pcwatch` source.
- Use mocked scraper classes and mocked watchlist/storage helpers.
- Ensure existing tool schema and serialization tests still pass.

## Dependencies
- Blocks: None
- Blocked by: [006, 007]
- Parallelizable with: [013, 015]

## Success Criteria (5 points)
1. `research_company` tests cover scraper loading and result merging.
2. `resolve_company` test verifies the watchlist is upserted.
3. Source-filtering tests include the `pcwatch` source.
4. Mock scraper returns predictable results without calling external services.
5. Existing tool schema and serialization tests continue to pass.

## Status
[014-testing-tools-updates-status.md](../status/014-testing-tools-updates-status.md)
