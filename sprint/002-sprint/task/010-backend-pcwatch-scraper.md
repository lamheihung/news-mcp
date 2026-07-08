# Task 010: Backend - pcwatch Scraper Plugin

## Description
Implement the `PcwatchScraper` plugin that searches PC Watch for a company, caches articles, and reports completeness.

## Requirements
- Create `PcwatchScraper` in `scrapers/pcwatch/__init__.py` inheriting from `BaseScraper`.
- `fetch_articles` loads watchlist search terms for the ticker and source, falls back to `Company.name`, searches all terms, deduplicates by URL, filters by `DateRange`, saves new articles, and updates `exhausted_before`.
- Stop paginating a search term once results are older than `DateRange.start`.
- Skip already-cached articles by checking title hash before opening the article page.
- `is_complete` returns `True` when `DateRange.start >= exhausted_before[source_id]`.

## Dependencies
- Blocks: [013, 014, 015]
- Blocked by: [001, 002, 003, 004, 005, 008, 009]
- Parallelizable with: [006, 007]

## Success Criteria (5 points)
1. `fetch_articles` returns `list[Article]` for a known company on pcwatch.
2. Duplicate URLs across multiple search terms are merged into a single article.
3. Articles with `published_at` outside `DateRange` are excluded from results.
4. `is_complete` returns `True` when `DateRange.start` is on or after the stored `exhausted_before` date.
5. New articles are saved to `data/{ticker}/pcwatch/{title_hash}.md`.

## Status
[010-backend-pcwatch-scraper-status.md](../status/010-backend-pcwatch-scraper-status.md)
