# Task 012: Testing - Scraper Loader and Base Class

## Description
Write unit tests for the scraper loader and the typed `BaseScraper` abstract base class.

## Requirements
- Test `load_scraper` success and failure paths.
- Test that `BaseScraper` cannot be instantiated and enforces abstract methods.
- Test a minimal concrete subclass can be instantiated and used.
- Keep tests independent of Playwright and browser binaries.

## Dependencies
- Blocks: None
- Blocked by: [004, 005]
- Parallelizable with: [011]

## Success Criteria (5 points)
1. `load_scraper` success and failure paths are tested.
2. `BaseScraper` abstract-method enforcement is tested.
3. A minimal concrete scraper subclass can be instantiated and called.
4. Tests run without Playwright installed.
5. Coverage for `scraper_loader.py` and `scraper_base.py` is at least 90%.

## Status
[012-testing-scraper-loader-status.md](../status/012-testing-scraper-loader-status.md)
