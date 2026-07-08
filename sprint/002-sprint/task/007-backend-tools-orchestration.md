# Task 007: Backend - Tools Orchestration

## Description
Update `research_company` to coordinate watchlist updates, scraper loading, completeness checks, article fetching, and result merging.

## Requirements
- Update the watchlist with the requested company before scraping.
- Filter configured sources by the optional `sources` parameter.
- For each selected source, load its scraper module via `scraper_loader`.
- Check `is_complete` before calling `fetch_articles`; skip fetch when cached articles already cover the range.
- Merge fetched and cached articles, deduplicate by URL, and sort by `published_at` descending.
- Keep the existing `example` source mock fallback when no real scraper is available.

## Dependencies
- Blocks: [014, 015]
- Blocked by: [002, 003, 005, 006]
- Parallelizable with: None

## Success Criteria (5 points)
1. `research_company` loads scraper modules dynamically from `config.yaml`.
2. Source filtering honors the optional `sources` parameter.
3. `is_complete` is checked before `fetch_articles` is invoked.
4. Returned articles are merged, deduplicated by URL, and sorted by `published_at` descending.
5. The `example` source still returns mock articles when its scraper is absent.

## Status
[007-backend-tools-orchestration-status.md](../status/007-backend-tools-orchestration-status.md)
