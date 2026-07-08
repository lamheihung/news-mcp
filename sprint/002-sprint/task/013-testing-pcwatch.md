# Task 013: Testing - pcwatch Scraper

## Description
Write unit and optional integration tests for the pcwatch browser helpers and `PcwatchScraper` plugin.

## Requirements
- Unit-test `search_results` and `extract_article` with mocked Playwright pages.
- Unit-test `PcwatchScraper.fetch_articles` and `is_complete` with mocked browser helpers, watchlist, and storage.
- Provide optional integration tests that hit the real pcwatch site, skipping when Playwright or a browser is unavailable.
- Verify filtering of `/docs/news/todays_sales/` URLs and date-range behavior.

## Dependencies
- Blocks: None
- Blocked by: [008, 009, 010]
- Parallelizable with: [014]

## Success Criteria (5 points)
1. Unit tests mock Playwright page objects and verify selector usage.
2. `extract_article` parses a sample pcwatch article HTML correctly.
3. `fetch_articles` uses watchlist search terms and storage helpers as expected.
4. Integration tests skip gracefully when Playwright or browser binaries are unavailable.
5. Coverage for `scrapers/pcwatch/` is at least 80%.

## Status
[013-testing-pcwatch-status.md](../status/013-testing-pcwatch-status.md)
