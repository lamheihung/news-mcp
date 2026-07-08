# Task 002: Backend - Watchlist Persistence

## Description
Implement load, save, upsert, and query helpers for the automatic watchlist stored at `data/watchlist.yaml`.

## Requirements
- Implement `load_watchlist(path)` that returns `list[WatchlistEntry]`, creating an empty file when missing.
- Implement `save_watchlist(entries, path)` that writes YAML atomically.
- Implement `upsert_company(entries, company)` that adds or updates a company entry while preserving existing `search_terms` and `exhausted_before`.
- Implement `get_search_terms(entries, ticker, source_id)` and `set_exhausted_before(entries, ticker, source_id, value)` helpers.
- Implement `get_exhausted_before(entries, ticker, source_id) -> date | None`.

## Dependencies
- Blocks: [006, 007, 009, 010, 011]
- Blocked by: [001]
- Parallelizable with: [003, 004, 005]

## Success Criteria (5 points)
1. `load_watchlist` creates an empty file when missing and returns `[]`.
2. `upsert_company` adds a new entry and updates an existing entry without overwriting `search_terms`.
3. `get_search_terms` returns source-specific terms or an empty list when none exist.
4. `set_exhausted_before` persists a date and `get_exhausted_before` reads it back correctly.
5. `save_watchlist` produces YAML that reloads to equivalent `WatchlistEntry` objects.

## Status
[002-backend-watchlist-persistence-status.md](../status/002-backend-watchlist-persistence-status.md)
