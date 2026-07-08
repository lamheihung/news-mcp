# Task 001: Backend - Watchlist Model

## Description
Add the `WatchlistEntry` Pydantic model to `src/models.py` so the server can track resolved companies and their per-source search terms.

## Requirements
- Add `WatchlistEntry` to `src/models.py` with fields defined in `architecture/002-architecture-design.md`.
- `search_terms` maps source ID strings to lists of search-term strings.
- `exhausted_before` maps source ID strings to `date` values.
- Existing models (`Company`, `Source`, `Article`, `DateRange`) remain unchanged and import cleanly.

## Dependencies
- Blocks: [002, 006, 009, 010]
- Blocked by: None
- Parallelizable with: [003, 004, 008]

## Success Criteria (5 points)
1. `WatchlistEntry` class exists in `src/models.py` and imports without errors.
2. `WatchlistEntry` validates `search_terms` as `dict[str, list[str]]`.
3. `WatchlistEntry` validates `exhausted_before` as `dict[str, date]`.
4. Instantiation rejects missing required fields and invalid types.
5. Existing `Company`, `Source`, `Article`, and `DateRange` models remain unchanged.

## Status
[001-backend-watchlist-model-status.md](../status/001-backend-watchlist-model-status.md)
