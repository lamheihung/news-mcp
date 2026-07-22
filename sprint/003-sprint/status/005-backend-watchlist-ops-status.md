# Status: Task 005

## Progress
- Percentage: 100%
- State: Complete

## Notes / Blockers
- Task completed. Added `set_search_terms` and `clear_exhausted_before` helpers to `src/watchlist.py`.
- All pre-commit hooks pass.

## Last Updated
2026-07-15

## Implementation Log
- Added `set_search_terms(entries, ticker, source_id, terms)` that replaces terms and clears the source exhaustion marker.
- Added `clear_exhausted_before(entries, ticker, source_id)` that removes the exhaustion marker.
- Both helpers raise `ValueError` when the company is not in the watchlist.
- Added comprehensive tests for both helpers in `tests/test_watchlist.py`.
