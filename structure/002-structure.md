# Structure v002

Created from: `architecture/002-architecture-design.md`

## Created

- `src/scraper_base.py` — `BaseScraper` abstract base class.
- `src/watchlist.py` — placeholder for `data/watchlist.yaml` helpers.
- `src/storage.py` — placeholder for deterministic article-cache helpers.
- `src/scraper_loader.py` — placeholder for dynamic scraper module loading.
- `scrapers/__init__.py` — scraper package marker.
- `scrapers/pcwatch/__init__.py` — placeholder for `PcwatchScraper`.
- `scrapers/pcwatch/browser.py` — placeholder for Playwright browser helpers.
- `tests/scrapers/__init__.py` — test package marker.
- `tests/scrapers/test_pcwatch.py` — placeholder for pcwatch scraper tests.
- `data/watchlist.yaml` — empty automatic watchlist starter file.
- `structure/002-structure.md` (this file).

## Modified

- `config.yaml` — added the `pcwatch` source registration alongside the existing `example` source.

## Removed

- None.

## Notes

All new Python modules contain only docstrings / placeholder comments. Implementation is handled by `/implement`.
