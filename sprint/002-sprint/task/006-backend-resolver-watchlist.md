# Task 006: Backend - Resolver Watchlist Update

## Description
Update the company resolver to persist every successfully resolved company into the automatic watchlist.

## Requirements
- After a successful Gemini resolution, upsert the resulting `Company` into `data/watchlist.yaml`.
- Preserve any existing `search_terms` and `exhausted_before` values for that ticker.
- Do not modify the watchlist when resolution fails.
- Keep existing resolver error handling and validation unchanged.

## Dependencies
- Blocks: [007, 014, 015]
- Blocked by: [001, 002]
- Parallelizable with: [003, 004, 005]

## Success Criteria (5 points)
1. `resolve_company` creates a `WatchlistEntry` with `bloomberg_ticker`, `name`, and `aliases`.
2. Re-resolving the same company preserves existing `search_terms` and `exhausted_before`.
3. The watchlist file is created automatically when it does not exist.
4. Failed resolution (missing key, API error, bad response) does not modify the watchlist.
5. Unit tests verify watchlist update using a mocked Gemini client.

## Status
[006-backend-resolver-watchlist-status.md](../status/006-backend-resolver-watchlist-status.md)
