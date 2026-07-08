# Task 004: Backend - Scraper Base Class

## Description
Define a typed abstract base class that all source-specific scraper plugins must implement.

## Requirements
- Update `src/scraper_base.py` with a typed `BaseScraper` abstract class.
- Declare abstract async methods `fetch_articles` and `is_complete`.
- Method signatures must accept `Source`, `Company`, and `DateRange` models.
- `fetch_articles` returns `list[Article]`; `is_complete` returns `bool`.
- Module passes `mypy` strict type checking.

## Dependencies
- Blocks: [005, 009, 010, 012]
- Blocked by: None
- Parallelizable with: [001, 003, 008]

## Success Criteria (5 points)
1. `BaseScraper` is abstract and cannot be instantiated directly.
2. A subclass missing `fetch_articles` cannot be instantiated.
3. A subclass missing `is_complete` cannot be instantiated.
4. Method signatures match `Source`, `Company`, `DateRange`, `list[Article]`, and `bool`.
5. `mypy src/scraper_base.py` reports no type errors.

## Status
[004-backend-scraper-base-status.md](../status/004-backend-scraper-base-status.md)
