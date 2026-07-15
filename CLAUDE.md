# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) server** for investment analysts. It runs as a single Python process using FastMCP over stdio. Analysts interact through natural language in their LLM client; the server resolves company identifiers to Bloomberg tickers, fetches articles from developer-curated sources, and returns raw articles inline for the LLM to synthesize.

The **Sprint 001 foundation phase is complete**: data models, config loading, MCP tools, unit tests, and an integration smoke test are in place.

The **Sprint 002 persistence and scraping phase is also complete**: an automatic watchlist, article storage, a scraper plugin framework, and the first real scraper (`pcwatch`) are implemented.

## Common Commands

All commands use `uv`.

```bash
# Install dependencies
uv sync

# Install optional scraper dependencies (required for pcwatch and future scrapers)
uv sync --group scrapers

# Run the MCP server (stdio transport)
uv run main.py

# Run all tests
uv run pytest tests

# Run a single test file verbosely
uv run pytest tests/test_config.py -v

# Run tests with coverage
uv run pytest tests --cov=src --cov-report=term-missing

# Type checking
uv run mypy src tests

# Linting
uv run ruff check src tests

# Formatting (check)
uv run ruff format --check src tests

# Formatting (apply)
uv run ruff format src tests

# Security scan
uv run bandit -r src tests -f txt -s B101

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files

# Verify lock file is up to date
uv lock --locked
```

## Setup Required Before Running

```bash
cp .env.template .env
# Add GEMINI_API_KEY to .env
```

`config.yaml` defines the developer-curated sources. It is loaded at startup; a missing or malformed file is a startup-blocking error.

For the `pcwatch` scraper to work, Playwright must be installed:

```bash
uv sync --group scrapers
playwright install chromium
```

## Architecture

- **`main.py`** is the FastMCP entry point. It creates the `mcp` app via `create_app()`, registers tools, and runs the server over stdio.
- **`src/config.py`** loads and validates `config.yaml` into `Source` Pydantic models via `load_config(path)`. It fails fast with readable errors.
- **`src/models.py`** defines the canonical data models: `Company`, `Source`, `Article`, and `DateRange`. `DateRange` validates that `end >= start`.
- **`src/resolver.py`** normalizes any company identifier to a Bloomberg ticker using the Gemini API. It persists resolved companies to `data/watchlist.yaml` and raises `CompanyResolutionError` on missing key, API failure, or unparseable response.
- **`src/watchlist.py`** manages the automatic watchlist of resolved companies stored in `data/watchlist.yaml`.
- **`src/storage.py`** persists cached articles to `data/{bloomberg_ticker}/{source_name}/{title_hash}.md` and lists cached articles filtered by date range.
- **`src/scraper_base.py`** defines the `BaseScraper` interface that every scraper plugin must implement (`is_complete`, `fetch_articles`).
- **`src/scraper_loader.py`** dynamically loads a scraper module by dotted path and extracts its scraper class.
- **`src/tools.py`** exposes three MCP tools: `list_sources`, `resolve_company`, and `research_company`.
  - `research_company` builds a date range (defaulting to the last 6 months), ensures the ticker is in the watchlist, selects sources, and for each source either returns cached articles, invokes the source's scraper, or falls back to mock articles for the `example` source. Results are deduplicated by URL and sorted by `published_at` descending.
- **`scrapers/pcwatch/`** is the first production scraper plugin. It uses Playwright to fetch Japanese PC/tech articles from `pc.watch.impress.co.jp`. English translation is deferred.
- **`data/`** stores the automatic watchlist (`data/watchlist.yaml`) and cached articles (`data/{bloomberg_ticker}/{source_name}/{title_hash}.md`).

The server is designed so that sources are developer-curated: an analyst can only query sources registered in `config.yaml`. Adding a new source requires:

1. Adding the source to `config.yaml` with a unique `id` and `scraper_module`.
2. Implementing a matching module under `scrapers/` that exposes a `BaseScraper` subclass.

## Testing

Tests live in `tests/`:

- `test_models.py` — Pydantic model validation, including `DateRange`.
- `test_config.py` — `load_config` success and error paths.
- `test_resolver.py` — Gemini resolver parsing, error handling, watchlist persistence, and edge cases.
- `test_tools.py` — MCP tool handlers, orchestration, and FastMCP schema/serialization checks.
- `test_main.py` — `create_app()` config loading, tool registration, and startup.
- `test_watchlist.py` — watchlist load, save, and upsert behavior.
- `test_storage.py` — article persistence, listing, and date-range filtering.
- `test_scraper_loader.py` — scraper module loading and base-class validation.
- `test_scrapers/test_pcwatch.py` — pcwatch scraper unit and integration tests.
- `test_integration.py` — end-to-end smoke test over stdio. It exercises `list_tools`, `list_sources`, `resolve_company`, and `research_company`. The live Gemini call is skipped when `GEMINI_API_KEY` is missing or the API returns an error/times out.

## Quality Gates

The project enforces quality checks in CI and via pre-commit hooks:

- ruff format check
- ruff lint
- mypy type check
- bandit security scan (B101 skipped because pytest uses asserts)
- pytest with coverage
- runtime smoke test

See `.github/workflows/ci.yml` for the CI definition.

## Dependency Management

Runtime dependencies live in `[project] dependencies` in `pyproject.toml`. Dev dependencies (pytest, mypy, ruff, bandit, pre-commit, etc.) live in `[dependency-groups] dev`. Optional scraper dependencies such as Playwright live in `[dependency-groups] scrapers`. After changing either, run `uv lock` to regenerate `uv.lock`.

## Branching Convention

- Feature work for sprint tasks: `feature/sprint-XXX-task-YYY`.
- Documentation updates: `docs/...`.
- Test-only additions/fixes: `test/...`.
- All branches are merged into `master` via fast-forward merges.
