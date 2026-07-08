# Task 005: Backend - Scraper Loader

## Description
Implement dynamic import of scraper modules registered in `config.yaml` so `research_company` can load source-specific plugins.

## Requirements
- Implement `load_scraper(module_name: str)` in `src/scraper_loader.py` using `importlib`.
- Return the imported module on success.
- Raise a clear error when the module does not exist.
- Provide a helper to retrieve a scraper class from the module by convention.
- Keep the module free of Playwright dependencies.

## Dependencies
- Blocks: [007, 010, 012]
- Blocked by: [004]
- Parallelizable with: [002, 003]

## Success Criteria (5 points)
1. `load_scraper("scrapers.pcwatch")` imports the module successfully.
2. `load_scraper("scrapers.nonexistent")` raises `ModuleNotFoundError` with the module name.
3. The loader can retrieve the `PcwatchScraper` class once implemented.
4. Error messages clearly identify the requested module name.
5. Unit tests cover success and failure paths without requiring Playwright.

## Status
[005-backend-scraper-loader-status.md](../status/005-backend-scraper-loader-status.md)
