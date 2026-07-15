# Architecture Design v003

Last updated: 2026-07-14

## Covered Specs

- `specs/investment-research-mcp-server.md`
- `specs/pcwatch-scraper.md`
- `specs/operational-tools-and-rag.md`
- `architecture/001-architecture-design.md`
- `architecture/002-architecture-design.md`

## System Overview

The server remains a single Python process running FastMCP over stdio. Three new responsibilities are added on top of v002:

1. **Embeddings** — local sentence-transformer model for question/article vectorization.
2. **RAG ranking** — filter returned articles by cosine similarity to the analyst’s question.
3. **Operational tools** — inspect and mutate watchlist/search/cache state directly through MCP tools.

```
[LLM Client / Claude Desktop] ← stdio → [FastMCP Server]
                                                  │
                    ┌─────────────────────────────┼──────────────┐
                    ↓                             ↓              ↓
              [config.yaml]                [Gemini API]     [Tool handlers]
                    │                        (resolver)            │
                    ↓                                              ↓
            [Source registry]                          [Watchlist / Storage]
                    │                                              │
                    │                              ┌───────────────┘
                    │                              ↓
                    │                        [Embeddings / RAG]
                    │                              │
                    └──────────────→ [scrapers/pcwatch] ←─────────┘
                                          │
                                          ↓
                                  [Playwright browser]
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| MCP Framework | FastMCP 3.x | Already in use; no change. |
| Browser automation | Playwright | Already used for pcwatch; no change. |
| Data models | Pydantic | Already used; new return models added. |
| Config / watchlist | YAML | Already used; no change. |
| File storage | Local filesystem (`data/`) | Already used; embeddings added to frontmatter. |
| LLM client | `google-genai` | Already used for `resolve_company`. |
| Embeddings | `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) | Spec requirement; supports Japanese/English; local CPU inference. |
| Similarity computation | Pure Python | Avoids adding or assuming `numpy`; simple enough for the expected corpus size. |

## Component Design

### `main.py` (project root)

- **Responsibility:** FastMCP app initialization, tool registration, and server startup.
- **Interfaces:** `create_app(config_path: Path) -> FastMCP`; runs `mcp.run(transport="stdio")`.
- **Dependencies:** `src.tools`, FastMCP.
- **Notes:** No structural change.

### `src/config.py`

- **Responsibility:** Load and validate `config.yaml` into `Source` models.
- **Interfaces:** `load_config(path: Path) -> list[Source]`.
- **Dependencies:** Pydantic, PyYAML, `src.models`.
- **Notes:** No change from v002.

### `src/models.py`

- **Responsibility:** Define Pydantic data models used across the server.
- **Interfaces:**
  - `Company`, `Source`, `Article`, `DateRange`, `WatchlistEntry` (existing)
  - `Article.relevance_score: float | None = None` (new)
  - `SourceStatus` (new): `{source_id, search_terms, exhausted_before, cached_article_count}`
  - `CompanyStatus` (new): `{bloomberg_ticker, name, aliases, sources: dict[str, SourceStatus]}`
  - `ResearchDiagnostics` (new): `{bloomberg_ticker, source_id, date_range, search_terms, exhausted_before, is_complete, cached_article_count, planned_action, reason}`
- **Dependencies:** Pydantic.

### `src/embeddings.py` (new)

- **Responsibility:** Load the local embedding model lazily and expose a simple embedding function.
- **Interfaces:**
  - `embed(text: str) -> list[float]`
  - `is_available() -> bool`
- **Dependencies:** `sentence-transformers`.
- **Notes:** Model is loaded on first call to avoid slowing down server startup. Failures are logged and re-raised so callers can fall back to non-RAG behavior.

### `src/rag.py` (new)

- **Responsibility:** Rank articles by semantic similarity to a question.
- **Interfaces:**
  - `ensure_embeddings(articles: list[Article]) -> list[Article]` — embed any article whose stored file lacks an embedding vector.
  - `rank_articles(question: str, articles: list[Article], top_k: int) -> list[Article]` — embed the question, score each article by cosine similarity, attach `relevance_score`, and return the top-K articles sorted by score descending.
- **Dependencies:** `src.embeddings`, `src.storage`, `src.models`.
- **Notes:** If embedding fails, returns the input articles unchanged so `research_company` can fall back to date sorting. Cosine similarity is implemented in pure Python to avoid a `numpy` dependency.

### `src/storage.py`

- **Responsibility:** Read/write cached articles; deterministic paths.
- **Interfaces:**
  - Existing: `article_path`, `article_exists`, `load_article`, `save_article`, `list_cached_articles`
  - Updated `save_article(article)` — writes `embedding` to frontmatter if present.
  - Updated `load_article(path)` — reads `embedding` from frontmatter if present.
- **Dependencies:** Pydantic, PyYAML, `src.models`.
- **Notes:** Frontmatter gains an `embedding: [float, ...]` field. Old articles without embeddings are embedded on demand by `src.rag.ensure_embeddings`.

### `src/watchlist.py`

- **Responsibility:** Load/save/update `data/watchlist.yaml`.
- **Interfaces:**
  - Existing: `load_watchlist`, `save_watchlist`, `upsert_company`, `get_search_terms`, `get_exhausted_before`, `set_exhausted_before`
  - New: `set_search_terms(entries, ticker, source_id, terms) -> list[WatchlistEntry]` — replaces terms and clears exhaustion.
  - New: `clear_exhausted_before(entries, ticker, source_id) -> list[WatchlistEntry]` — removes the exhaustion marker.
- **Dependencies:** Pydantic, PyYAML, `src.models`.

### `src/tools.py`

- **Responsibility:** Implement MCP tool handlers and orchestrate scrapers, storage, and RAG.
- **Interfaces:**
  - Existing: `list_sources`, `resolve_company`, `research_company`, `register_tools`
  - Updated `research_company(..., use_rag: bool = true, top_k: int = 10)` — after merging articles, optionally calls `src.rag.rank_articles`.
  - New: `get_company_status(bloomberg_tickers: list[str]) -> list[CompanyStatus]`
  - New: `set_search_terms(bloomberg_ticker, source_id, terms) -> CompanyStatus`
  - New: `reset_source_cache(bloomberg_ticker, source_id, delete_cached_articles) -> CompanyStatus`
  - New: `get_research_diagnostics(bloomberg_ticker, source_id?, start_date?, end_date?) -> list[ResearchDiagnostics]`
- **Dependencies:** `src.config`, `src.resolver`, `src.models`, `src.watchlist`, `src.storage`, `src.scraper_loader`, `src.rag`.
- **Notes:** Adds structured logging for tool calls, scraper decisions, and cache state.

### `src/scraper_loader.py`

- **Responsibility:** Dynamically import scraper modules.
- **Interfaces:** No change.
- **Dependencies:** `importlib`.

### `src/scraper_base.py`

- **Responsibility:** Abstract base class for scrapers.
- **Interfaces:** No change.

### `scrapers/pcwatch/__init__.py`

- **Responsibility:** pcwatch-specific scraping logic.
- **Interfaces:** No change.
- **Notes:** Updated exhaustion logic. `set_exhausted_before` is only called when at least one article is saved within the requested date range. If zero articles are found, no marker is written.

### `scrapers/pcwatch/browser.py`

- **Responsibility:** Playwright browser helpers.
- **Interfaces:** No change.
- **Notes:** No change.

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
  - `relevance_score`: `float | None` — cosine similarity when RAG is used.
- `DateRange` (internal):
  - `start`: `date`
  - `end`: `date`
- `WatchlistEntry`:
  - `bloomberg_ticker`: `str`
  - `name`: `str`
  - `aliases`: `list[str]`
  - `search_terms`: `dict[str, list[str]]`
  - `exhausted_before`: `dict[str, date]`
- `SourceStatus` (new):
  - `source_id`: `str`
  - `search_terms`: `list[str]`
  - `exhausted_before`: `date | None`
  - `cached_article_count`: `int`
- `CompanyStatus` (new):
  - `bloomberg_ticker`: `str`
  - `name`: `str`
  - `aliases`: `list[str]`
  - `sources`: `dict[str, SourceStatus]`
- `ResearchDiagnostics` (new):
  - `bloomberg_ticker`: `str`
  - `source_id`: `str`
  - `date_range`: `DateRange`
  - `search_terms`: `list[str]`
  - `exhausted_before`: `date | None`
  - `is_complete`: `bool`
  - `cached_article_count`: `int`
  - `planned_action`: `str`
  - `reason`: `str`

Relationships:
- `CompanyStatus` → contains multiple `SourceStatus` (one per configured source).
- `ResearchDiagnostics` → describes one `(Company, Source)` pair; the tool always returns a list for consistency.
- `Article` → belongs to one `Source` and one `Company`.

## API Design

### `list_sources()`

- **Returns:** `list[Source]`
- **Description:** Returns all sources loaded from `config.yaml`.

### `resolve_company(identifier: str)`

- **Parameters:** `identifier` — any company name or ticker.
- **Returns:** `Company`
- **Description:** Calls Gemini API and updates the automatic watchlist.

### `research_company(bloomberg_ticker, question, start_date, end_date, sources, use_rag, top_k)`

- **Parameters:**
  - `bloomberg_ticker`: `str`
  - `question`: `str | None`
  - `start_date`: `str | None`
  - `end_date`: `str | None`
  - `sources`: `list[str] | None`
  - `use_rag`: `bool = true`
  - `top_k`: `int = 10`
- **Returns:** `list[Article]`
- **Description:** Fetches articles by source/date range, optionally ranks by question relevance, and returns top-K results with `relevance_score`.

### `get_company_status(bloomberg_tickers: list[str])`

- **Parameters:** `bloomberg_tickers` — list of canonical tickers.
- **Returns:** `list[CompanyStatus]`
- **Description:** Returns watchlist metadata and per-source cache counts.

### `set_search_terms(bloomberg_ticker, source_id, terms)`

- **Parameters:**
  - `bloomberg_ticker`: `str`
  - `source_id`: `str`
  - `terms`: `list[str]`
- **Returns:** `CompanyStatus`
- **Description:** Updates search terms for a company/source and clears the source’s exhaustion marker.

### `reset_source_cache(bloomberg_ticker, source_id, delete_cached_articles)`

- **Parameters:**
  - `bloomberg_ticker`: `str`
  - `source_id`: `str`
  - `delete_cached_articles`: `bool = false`
- **Returns:** `CompanyStatus`
- **Description:** Clears the exhaustion marker and optionally deletes cached `.md` files for that source.

### `get_research_diagnostics(bloomberg_ticker, source_id, start_date, end_date)`

- **Parameters:**
  - `bloomberg_ticker`: `str`
  - `source_id`: `str | None`
  - `start_date`: `str | None`
  - `end_date`: `str | None`
- **Returns:** `list[ResearchDiagnostics]` — one entry per source. If `source_id` is provided, the list contains one item.
- **Description:** Reports planned action, cache status, and reason without scraping.

## Key Decisions

### Dedicated `src/rag.py` module

- **Decision:** Place RAG logic (embedding, similarity, ranking) in a dedicated `src/rag.py` module rather than inline in `src/tools.py`.
- **Rationale:** Keeps `src/tools.py` focused on MCP tool orchestration; makes RAG logic independently testable.
- **Trade-offs:** One more module to maintain.

### Dedicated `src/embeddings.py` module

- **Decision:** Isolate the sentence-transformers model loading and embedding call in `src/embeddings.py`.
- **Rationale:** Centralizes the heavy dependency; other modules call a simple `embed(text)` interface.
- **Trade-offs:** Adds one module.

### Store embeddings in `.md` frontmatter

- **Decision:** Add an `embedding` field to the YAML frontmatter of each cached article.
- **Rationale:** Keeps article text and its vector together; no sidecar files or database needed.
- **Trade-offs:** Each file grows by ~384 floats; old articles without embeddings must be embedded on demand.

### Pure Python cosine similarity

- **Decision:** Implement cosine similarity without `numpy`.
- **Rationale:** Avoids adding or assuming a `numpy` dependency; the expected corpus size makes pure Python fast enough.
- **Trade-offs:** Slightly more code than a one-line `numpy` call; may become a bottleneck if the corpus grows past thousands of articles.

### Embed articles at scrape time

- **Decision:** Embed and store article vectors when articles are first saved.
- **Rationale:** Keeps `research_company` fast; embedding happens once per article.
- **Trade-offs:** First scrape after enabling RAG is slower because each article is embedded.

### RAG is opt-out per call

- **Decision:** `use_rag` defaults to `true`; set to `false` to disable relevance ranking.
- **Rationale:** Encourages relevance filtering by default while preserving existing behavior when disabled.
- **Trade-offs:** Analysts may occasionally want all articles and must explicitly set `use_rag=false`.

### `question` remains optional

- **Decision:** `research_company.question` stays optional.
- **Rationale:** Preserves backward compatibility and supports “show me recent articles” style queries.
- **Trade-offs:** When no question is provided, results are not relevance-ranked.

### Operational tools update state directly

- **Decision:** `set_search_terms` and `reset_source_cache` execute immediately when called.
- **Rationale:** Changes are reversible with another tool call, so confirmation adds friction.
- **Trade-offs:** A misinterpreted LLM call could temporarily change search terms.

### `set_search_terms` clears exhaustion in `src/watchlist.py`

- **Decision:** The watchlist helper both updates terms and clears the source exhaustion marker.
- **Rationale:** Encapsulates the invariant that new terms invalidate old coverage.
- **Trade-offs:** A single function does two things; acceptable because they always happen together.

### `get_research_diagnostics` always returns a list

- **Decision:** Return `list[ResearchDiagnostics]` regardless of whether `source_id` is provided.
- **Rationale:** Consistent with `get_company_status` and simpler for the LLM to handle.
- **Trade-offs:** Single-source diagnostics require indexing into a one-item list.

### Exhaustion fix lives in pcwatch scraper

- **Decision:** Only `PcwatchScraper` changes its exhaustion-marker behavior.
- **Rationale:** The spec targets pcwatch specifically; other scrapers may have different completeness guarantees.
- **Trade-offs:** If future scrapers have the same bug, the fix must be duplicated or moved to `BaseScraper`.

### Log to stderr only

- **Decision:** Add structured logging to stderr; no file logging.
- **Rationale:** Simplest integration with MCP server processes; avoids log file management.
- **Trade-offs:** Logs are not persisted to disk.

## Open Questions

- None.

## Risks & Mitigations

- **Risk:** `sentence-transformers` + `torch` significantly increases install size and cold-start time.
  - **Mitigation:** Keep embeddings lazy-loaded; document the dependency cost; consider lighter alternatives (e.g. `fastembed`) in a future iteration if size becomes problematic.
- **Risk:** First scrape after enabling RAG is slow because every article is embedded.
  - **Mitigation:** Embed articles at scrape time once; subsequent queries are fast.
- **Risk:** Embedding model not available on first run (download failure, missing disk space).
  - **Mitigation:** `src.embeddings.py` logs clear errors; `src.rag.py` falls back to returning unranked articles.
- **Risk:** Old `.md` files without embeddings break `load_article` or RAG.
  - **Mitigation:** `load_article` treats `embedding` as optional; `ensure_embeddings` computes missing vectors on demand.
- **Risk:** Long embeddings in YAML frontmatter make files hard to read.
  - **Mitigation:** Frontmatter is machine-readable; analysts interact through tools, not raw files.
- **Risk:** Pure Python similarity becomes slow as the corpus grows.
  - **Mitigation:** Migrate to `numpy` or a vector database once profiling shows a bottleneck.
