# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) server** for investment analysts. It runs as a single Python process using FastMCP over stdio. Analysts interact through natural language in their LLM client; the server resolves company identifiers to Bloomberg tickers, fetches articles from developer-curated sources, and returns raw articles inline for the LLM to synthesize.

The **Sprint 001 foundation phase is complete**: data models, config loading, MCP tools, unit tests, and an integration smoke test are in place. Article caching, storage, and source-specific scrapers are intentionally deferred to a later sprint.

## Common Commands

All commands use `uv`.

```bash
# Install dependencies
uv sync

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

## Architecture

- **`main.py`** is the FastMCP entry point. It creates the `mcp` app via `create_app()`, registers tools, and runs the server over stdio.
- **`src/config.py`** loads and validates `config.yaml` into `Source` Pydantic models via `load_config(path)`. It fails fast with readable errors.
- **`src/models.py`** defines the canonical data models: `Company`, `Source`, `Article`, and `DateRange`. `DateRange` validates that `end >= start`.
- **`src/resolver.py`** normalizes any company identifier to a Bloomberg ticker using the Gemini API. It raises `CompanyResolutionError` on missing key, API failure, or unparseable response.
- **`src/tools.py`** exposes three MCP tools: `list_sources`, `resolve_company`, and `research_company`. `research_company` currently returns mock articles filtered by date range and optional source IDs.
- **`scrapers/`** (deferred) will contain source-specific scraper plugins, each implementing `fetch_articles` and `is_complete`.
- **`data/`** (deferred) will store cached articles as `data/{bloomberg_ticker}/{source_name}/{title_hash}.md`.

The server is designed so that sources are developer-curated: an analyst can only query sources registered in `config.yaml`. Adding a new source requires implementing a matching scraper module.

## Testing

Tests live in `tests/`:

- `test_models.py` — Pydantic model validation, including `DateRange`.
- `test_config.py` — `load_config` success and error paths.
- `test_resolver.py` — Gemini resolver parsing, error handling, and edge cases.
- `test_tools.py` — MCP tool handlers and FastMCP schema/serialization checks.
- `test_main.py` — `create_app()` config loading, tool registration, and startup.
- `test_integration.py` — end-to-end smoke test over stdio. It exercises `list_tools`, `list_sources`, `resolve_company`, and `research_company`. The live Gemini call is skipped when `GEMINI_API_KEY` is missing or the API returns an error/times out.

## Quality Gates

The project enforces quality checks in CI and via pre-commit hooks:

- ruff format check
- ruff lint
- mypy type check
- bandit security scan (B101 skipped because pytest uses asserts)
- pytest with coverage
- runtime smoke test

See `QUALITY_CHECKLIST.md` for the full list and `.github/workflows/ci.yml` for the CI definition.

## Dependency Management

Runtime dependencies live in `[project] dependencies` in `pyproject.toml`. Dev dependencies (pytest, mypy, ruff, bandit, pre-commit, etc.) live in `[dependency-groups] dev`. After changing either, run `uv lock` to regenerate `uv.lock`.

## Branching Convention

- Feature work for sprint tasks: `feature/sprint-XXX-task-YYY`.
- Documentation updates: `docs/...`.
- Test-only additions/fixes: `test/...`.
- All branches are merged into `master` via fast-forward merges.
