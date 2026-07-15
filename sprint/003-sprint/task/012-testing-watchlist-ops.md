# Task 012: Testing - Watchlist Operational Helpers

## Description
Write unit tests for the new watchlist helpers in `src/watchlist.py`.

## Requirements
- Test `set_search_terms` updates terms and clears exhaustion.
- Test `clear_exhausted_before` removes the marker.
- Test error handling for companies not in the watchlist.
- Test YAML persistence of watchlist mutations.

## Dependencies
- Blocks: []
- Blocked by: [005]
- Parallelizable with: [010, 011]

## Success Criteria (5 points)
1. `set_search_terms` test verifies term replacement and exhaustion marker clearance.
2. `clear_exhausted_before` test verifies marker removal.
3. Missing-company cases raise the expected `ValueError`.
4. Watchlist save/load round-trip preserves updated terms and markers.
5. Test coverage for `src/watchlist.py` reaches at least 85%.

## Status
[012-testing-watchlist-ops-status.md](../status/012-testing-watchlist-ops-status.md)
