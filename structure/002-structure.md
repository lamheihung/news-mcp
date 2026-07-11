# Structure v002

Created from: `architecture/002-architecture-design.md`

## Created

- `src/scraper_base.py` — `BaseScraper` abstract base class.
- `src/watchlist.py` — helpers for loading, saving, and updating `data/watchlist.yaml`.
- `src/storage.py` — deterministic article-cache helpers (`article_path`, `save_article`, `load_article`, `list_cached_articles`).
- `src/scraper_loader.py` — dynamic scraper module loading (`load_scraper`, `get_scraper_class`).
- `scrapers/__init__.py` — scraper package marker.
- `scrapers/pcwatch/__init__.py` — `PcwatchScraper` plugin implementing `BaseScraper`.
- `scrapers/pcwatch/browser.py` — Playwright browser helpers for pcwatch search and article extraction.
- `tests/test_scrapers/__init__.py` — test package marker.
- `tests/test_scrapers/test_pcwatch.py` — pcwatch scraper unit and integration tests.
- `tests/test_storage.py` — article storage helper tests.
- `tests/test_watchlist.py` — watchlist helper tests.
- `tests/test_scraper_loader.py` — scraper loader and base class tests.
- `data/watchlist.yaml` — automatic watchlist starter file.
- `structure/002-structure.md` (this file).

## Modified

- `config.yaml` — added the `pcwatch` source registration alongside the existing `example` source.
- `src/models.py` — added `WatchlistEntry` and `published_at_sort_key` helper.
- `src/resolver.py` — now persists resolved companies to the automatic watchlist.
- `src/tools.py` — `research_company` now orchestrates scrapers, caches articles, and merges results.
- `src/storage.py` — implemented article persistence and cache listing.
- `tests/test_integration.py` — extended smoke test to cover the pcwatch source path.

## Removed

- None.

## Notes

All modules listed above are fully implemented and covered by tests. Manual testing confirmed the pcwatch scraper works for SK hynix, TSMC, NVIDIA, and Micron.
