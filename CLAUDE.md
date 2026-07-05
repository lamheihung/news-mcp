# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) server** for investment analysts. It runs as a single Python process using FastMCP over stdio. Analysts interact through natural language in their LLM client; the server resolves company identifiers to Bloomberg tickers, fetches articles from developer-curated sources, and returns raw articles inline for the LLM to synthesize.

The project is currently in the **foundation phase**: data models, config loading, and MCP tools are being built. Article caching, storage, and source-specific scrapers are intentionally deferred.

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

- **`main.py`** is the FastMCP entry point. It creates the `mcp` app and runs it with stdio transport. Tool handlers are registered here (or imported from `src.tools`).
- **`src/config.py`** loads and validates `config.yaml` into `Source` Pydantic models via `load_config(path)`. It fails fast with readable errors.
- **`src/models.py`** defines the canonical data models: `Company`, `Source`, `Article`, and `DateRange`. `DateRange` validates that `end >= start`.
- **`src/resolver.py`** (to be implemented) normalizes any company identifier to a Bloomberg ticker using the Gemini API.
- **`src/tools.py`** (to be implemented) exposes three MCP tools: `list_sources`, `resolve_company`, and `research_company`. In the foundation phase, `research_company` returns mock articles.
- **`scrapers/`** (deferred) will contain source-specific scraper plugins, each implementing `fetch_articles` and `is_complete`.
- **`data/`** (deferred) will store cached articles as `data/{bloomberg_ticker}/{source_name}/{title_hash}.md`.

The server is designed so that sources are developer-curated: an analyst can only query sources registered in `config.yaml`. Adding a new source requires implementing a matching scraper module.

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

Features are developed on `feature/sprint-XXX-task-YYY` branches and merged into `master` via fast-forward merges.
