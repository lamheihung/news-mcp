# Task 009: Backend - pcwatch Browser Helpers

## Description
Implement Playwright browser helpers that extract pcwatch search results and full article content.

## Requirements
- Implement `search_results(page, term, stop_before)` returning URLs, titles, and snippet dates.
- Sort search by newest date and paginate until the snippet date is older than `stop_before`.
- Skip result URLs containing `/docs/news/todays_sales/`.
- Implement `extract_article(page, url, bloomberg_ticker, source_id)` returning an `Article`.
- Parse title from `article h1`, author from `article .article-info ul.author.list li`, datetime from `article .article-info .publish-date`, and content from `article .main-contents` excluding `.related-links`/`.relatedLinks` and ad blocks.
- Run headless by default; enable headed mode via an environment variable for debugging.
- Enforce polite delays between page requests.

## Dependencies
- Blocks: [010, 013]
- Blocked by: [001, 003, 004, 008]
- Parallelizable with: None

## Success Criteria (5 points)
1. `search_results` extracts at least one result for a known pcwatch search term.
2. `extract_article` parses the publish date in `YYYY年M月D日 HH:MM` format.
3. Extracted content excludes `.related-links` and ad blocks.
4. URLs containing `/docs/news/todays_sales/` are excluded from search results.
5. Headed mode is toggleable via an environment variable.

## Status
[009-backend-pcwatch-browser-status.md](../status/009-backend-pcwatch-browser-status.md)
