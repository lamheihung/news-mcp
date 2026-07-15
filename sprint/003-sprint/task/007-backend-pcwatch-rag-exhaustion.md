# Task 007: Backend - pcwatch RAG and Exhaustion Fix

## Description
Update the `pcwatch` scraper to embed articles at scrape time and only mark a date range as exhausted when articles are actually found within it.

## Requirements
- Embed each new article before saving and include the vector on the `Article` model.
- Only call `set_exhausted_before` when at least one article is saved inside the requested date range.
- Add structured logging for search terms used, articles saved, and exhaustion decisions.
- Keep existing browser automation and search-result handling unchanged.

## Dependencies
- Blocks: [009, 014, 016]
- Blocked by: [001, 003, 004, 005]
- Parallelizable with: [006, 008]

## Success Criteria (5 points)
1. Saved articles contain an `embedding` vector in their frontmatter.
2. `exhausted_before` is not written when zero articles are found in the requested range.
3. `exhausted_before` is written to `date_range.start` when at least one article is saved in range.
4. Structured logs include the search term, saved article count, and exhaustion decision.
5. Existing `pcwatch` unit and integration tests continue to pass.

## Status
[007-backend-pcwatch-rag-exhaustion-status.md](../status/007-backend-pcwatch-rag-exhaustion-status.md)
