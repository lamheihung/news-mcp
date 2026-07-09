# Status: Task 006

## Progress
- Percentage: 100%
- State: Completed

## Notes / Blockers
- No blockers.

## Last Updated
2026-07-09

## Implementation Log
- Task created during sprint 002 decomposition.
- Updated `src/resolver.py` to upsert resolved companies into `data/watchlist.yaml`.
- Added `WATCHLIST_PATH` constant and `_upsert_watchlist` helper.
- Preserved existing `search_terms` and `exhausted_before` on re-resolution.
- Ensured failed resolutions do not modify the watchlist.
- Updated `tests/test_resolver.py` with watchlist-aware fixtures and tests.
- `tests/test_resolver.py` passes (12/12).
- Full suite: 56 passed; only pre-existing `test_integration.py::test_server_smoke` fails due to `config.yaml` source count.
