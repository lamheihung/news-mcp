# Task 005: Backend - Watchlist Operational Helpers

## Description
Add watchlist helpers that let operational tools manage per-source search terms and exhaustion markers.

## Requirements
- Add `set_search_terms(entries, ticker, source_id, terms)` that replaces terms and clears the source's exhaustion marker.
- Add `clear_exhausted_before(entries, ticker, source_id)` that removes the exhaustion marker.
- Preserve existing `load_watchlist`, `save_watchlist`, `upsert_company`, and query helpers.
- Validate inputs and raise clear errors when the company is missing.

## Dependencies
- Blocks: [007, 008, 012]
- Blocked by: [001]
- Parallelizable with: [003, 004]

## Success Criteria (5 points)
1. `set_search_terms` replaces search terms and clears `exhausted_before` for the source.
2. `clear_exhausted_before` removes the exhaustion marker if it exists.
3. Both helpers raise `ValueError` for a company not present in the watchlist.
4. Watchlist YAML save/load round-trip preserves updated terms and markers.
5. Existing `tests/test_watchlist.py` cases continue to pass.

## Status
[005-backend-watchlist-ops-status.md](../status/005-backend-watchlist-ops-status.md)
