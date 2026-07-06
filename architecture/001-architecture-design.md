# Architecture Design v001

Last updated: 2026-07-06

## Covered Specs

- `specs/investment-research-mcp-server.md`

## System Overview

A single Python process running a FastMCP server over stdio. The foundation exposes three MCP tools: listing sources, resolving company identifiers, and researching companies. Article storage and scrapers are deferred to a later phase.

```
[LLM Client / Claude Desktop]  ← stdio →  [FastMCP Server]
                                                  │
                    ┌─────────────────────────────┼──────────────┐
                    ↓                             ↓              ↓
              [config.yaml]                [Gemini API]     [Tool handlers]
                    │                        (resolver)
                    ↓
            [Source registry]
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| MCP Framework | FastMCP 3.x | Already in `pyproject.toml`; simplest Python MCP option. |
| Transport | stdio | Easiest for local Claude Desktop; SSE later with one-line change. |
| Data Models | Pydantic | Native FastMCP support for params and return types. |
| Config | YAML | Human-readable for developer/operator. |
| LLM Client | `google-genai` | Gemini free tier for `resolve_company`. |

## Component Design

### `main.py` (project root)

- **Responsibility:** FastMCP app initialization, tool registration, and server startup.
- **Interfaces:** Runs `mcp.run(transport="stdio")`.
- **Dependencies:** `src.tools`, FastMCP.

### `src/config.py`

- **Responsibility:** Load and validate `config.yaml` into `Source` models.
- **Interfaces:** `load_config(path: Path) -> list[Source]`
- **Dependencies:** Pydantic, PyYAML, `src.models`.

### `src/models.py`

- **Responsibility:** Define Pydantic data models used across the server.
- **Interfaces:** `Company`, `Source`, `Article`, `DateRange`.
- **Dependencies:** Pydantic.

### `src/resolver.py`

- **Responsibility:** Call Gemini API to normalize any company identifier to a Bloomberg ticker.
- **Interfaces:** `resolve_company(identifier: str) -> Company`
- **Dependencies:** `google-genai`, `src.models`.
- **Note:** Requires `GEMINI_API_KEY` environment variable.

### `src/tools.py`

- **Responsibility:** Implement MCP tool handlers.
- **Interfaces:**
  - `list_sources() -> list[Source]`
  - `resolve_company(identifier: str) -> Company`
  - `research_company(bloomberg_ticker: str, question: str, start_date: str | None, end_date: str | None, sources: list[str] | None) -> list[Article]`
- **Dependencies:** `src.config`, `src.resolver`, `src.models`.
- **Note:** `research_company` returns mock/sample articles in the foundation phase. Real cache/scrape logic is added later.

## Data Model

- `Company`:
  - `bloomberg_ticker`: `str`
  - `name`: `str`
  - `aliases`: `list[str]`
- `Source`:
  - `id`: `str`
  - `name`: `str`
  - `base_url`: `str`
  - `scraper_module`: `str`
  - `description`: `str`
- `Article`:
  - `id`: `str`
  - `bloomberg_ticker`: `str`
  - `source_id`: `str`
  - `url`: `str`
  - `title`: `str`
  - `content`: `str`
  - `published_at`: `datetime`
  - `fetched_at`: `datetime`
  - `stored_path`: `Path`
- `DateRange` (internal):
  - `start`: `date`
  - `end`: `date`

## API Design

### `list_sources()`

- **Returns:** `list[Source]`
- **Description:** Returns all sources loaded from `config.yaml`.

### `resolve_company(identifier: str)`

- **Parameters:** `identifier` — any company name or ticker.
- **Returns:** `Company`
- **Description:** Calls Gemini API to normalize the identifier to a Bloomberg ticker.

### `research_company(bloomberg_ticker, question, start_date, end_date, sources)`

- **Parameters:**
  - `bloomberg_ticker`: `str` — canonical ticker.
  - `question`: `str` — analyst's question.
  - `start_date`: `str | None` — ISO date (`YYYY-MM-DD`), defaults to 6 months ago.
  - `end_date`: `str | None` — ISO date (`YYYY-MM-DD`), defaults to today.
  - `sources`: `list[str] | None` — optional source filter; defaults to all configured sources.
- **Returns:** `list[Article]`
- **Description:** Foundation phase returns mock articles. Future implementation will check cache and scrape missing articles.

## Key Decisions

### Entry point at root, modules under `src/`

- **Decision:** Keep `main.py` at the project root and place application code under `src/`.
- **Rationale:** Clean separation between entry point and implementation modules.
- **Trade-off:** Slightly more imports to manage; acceptable for clarity.

### stdio transport first

- **Decision:** Use stdio for initial development.
- **Rationale:** Easiest to test with Claude Desktop locally.
- **Trade-off:** Only local access; SSE can be added later without structural changes.

### Separate `start_date` and `end_date` parameters

- **Decision:** Use two ISO date string params instead of a nested `date_range` object.
- **Rationale:** LLMs supply simple primitive values more reliably.
- **Trade-off:** Slightly less structured; server converts to `DateRange` internally.

### Server owns article storage (deferred)

- **Decision:** The server will centrally manage article caching and storage; scrapers only fetch.
- **Rationale:** Consistent paths, duplicate prevention, and cache-aware logic live in one place.
- **Trade-off:** Storage module is deferred until the first scraper is built.

### Include `Article` model in foundation

- **Decision:** Define `Article` in `src/models.py` even though storage/scrapers are deferred.
- **Rationale:** Needed for `research_company` return type and future storage integration.
- **Trade-off:** Slightly more upfront modeling; avoids refactor later.

## Open Questions

- [x] Final structure of `config.yaml` for sources. — Finalized in Task 002; see `config.yaml`.
- [x] Mock article design (deferred to testing phase). — Implemented in Task 005/008; see `src/tools.py` and `tests/test_integration.py`.
- [ ] First real scraper source (deferred to a later sprint).

## Risks & Mitigations

- **Risk:** Gemini free-tier rate limits block ticker resolution.
  - **Mitigation:** Cache resolved tickers locally in a future iteration.
- **Risk:** LLM provides malformed dates.
  - **Mitigation:** Pydantic validation with clear error messages.
- **Risk:** `config.yaml` missing or malformed.
  - **Mitigation:** Validate at startup and fail fast with a readable error.
