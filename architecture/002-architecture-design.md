# Architecture Design v002

Last updated: 2026-07-08

## Covered Specs

- `specs/investment-research-mcp-server.md`
- `specs/pcwatch-scraper.md`
- `architecture/001-architecture-design.md`

## System Overview

The foundation remains a single Python process running a FastMCP server over stdio. We add three new responsibilities to support the first real scraper:

1. **Watchlist** — automatically track resolved/researched companies and their per-source search terms.
2. **Storage** — read/write cached articles at deterministic local paths.
3. **Scrapers** — source-specific browser automation plugins that implement a shared abstract base class.

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
                    └──────────────→ [scrapers/pcwatch] ←─────────┘
                                          │
                                          ↓
                                  [Playwright browser]
                                          │
                                          ↓
                                  [pc.watch.impress.co.jp]
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| MCP Framework | FastMCP 3.x | Already in use; no change. |
| Browser automation | Playwright | Handles JS-rendered Google Custom Search on pcwatch; used during exploration. |
| HTML/text extraction | Playwright selectors + stdlib | No additional parsing library needed because Playwright can extract text directly. |
| Data models | Pydantic | Native FastMCP support; already used across the codebase. |
| Config / watchlist | YAML | Human-readable; PyYAML already in dependencies. |
| File storage | Local filesystem (`data/`) | Matches existing spec and keeps the server self-contained. |
| LLM client | `google-genai` | Already in use for `resolve_company`. |

## Component Design

### `main.py` (project root)

- **Responsibility:** FastMCP app initialization, tool registration, and server startup.
- **Interfaces:** `create_app(config_path: Path) -> FastMCP`; runs `mcp.run(transport="stdio")`.
- **Dependencies:** `src.tools`, FastMCP.
- **Notes:** No structural change; continues to call `init_tools` and `register_tools`.

### `src/config.py`

- **Responsibility:** Load and validate `config.yaml` into `Source` models.
- **Interfaces:** `load_config(path: Path) -> list[Source]`.
- **Dependencies:** Pydantic, PyYAML, `src.models`.

### `src/models.py`

- **Responsibility:** Define Pydantic data models used across the server.
- **Interfaces:** `Company`, `Source`, `Article`, `DateRange`, and the new `WatchlistEntry`.
- **Dependencies:** Pydantic.

### `src/resolver.py`

- **Responsibility:** Call Gemini API to normalize any company identifier to a Bloomberg ticker.
- **Interfaces:** `resolve_company(identifier: str) -> Company`.
- **Dependencies:** `google-genai`, `src.models`, `src.watchlist`.
- **Notes:** Now updates the automatic watchlist after a successful resolution.

### `src/tools.py`

- **Responsibility:** Implement MCP tool handlers and orchestrate scrapers.
- **Interfaces:**
  - `list_sources() -> list[Source]`
  - `resolve_company(identifier: str) -> Company`
  - `research_company(bloomberg_ticker: str, question: str, start_date: str | None, end_date: str | None, sources: list[str] | None) -> list[Article]`
  - `register_tools(mcp: FastMCP) -> None`
- **Dependencies:** `src.config`, `src.resolver`, `src.models`, `src.watchlist`, `src.storage`, `src.scraper_loader`.
- **Notes:** `research_company` now resolves the requested sources, loads their scraper modules, checks `is_complete`, calls `fetch_articles` when needed, and merges results. The example source continues to return mock articles until a real scraper is implemented.

### `src/watchlist.py`

- **Responsibility:** Load/save `data/watchlist.yaml`; update it when `resolve_company` or `research_company` succeeds.
- **Interfaces:**
  - `load_watchlist(path: Path) -> list[WatchlistEntry]`
  - `save_watchlist(entries: list[WatchlistEntry], path: Path) -> None`
  - `upsert_company(entries: list[WatchlistEntry], company: Company) -> list[WatchlistEntry]`
  - `get_search_terms(entries: list[WatchlistEntry], ticker: str, source_id: str) -> list[str]`
  - `get_exhausted_before(entries: list[WatchlistEntry], ticker: str, source_id: str) -> date | None`
  - `set_exhausted_before(entries: list[WatchlistEntry], ticker: str, source_id: str, value: date) -> list[WatchlistEntry]`
- **Dependencies:** Pydantic, PyYAML, `src.models`.

### `src/storage.py`

- **Responsibility:** Read/write cached articles; compute deterministic title hashes.
- **Interfaces:**
  - `article_path(ticker: str, source_id: str, title: str) -> Path`
  - `article_exists(ticker: str, source_id: str, title: str) -> bool`
  - `load_article(path: Path) -> Article`
  - `save_article(article: Article) -> None`
  - `list_cached_articles(ticker: str, source_id: str, date_range: DateRange) -> list[Article]`
- **Dependencies:** Pydantic, `src.models`.
- **Notes:** Storage path is `data/{bloomberg_ticker}/{source_id}/{title_hash}.md`. Title hash is a deterministic SHA-256 truncated to 16 hex characters.

### `src/scraper_loader.py`

- **Responsibility:** Dynamically import scraper modules registered in `config.yaml`.
- **Interfaces:**
  - `load_scraper(module_name: str) -> Any`
- **Dependencies:** `importlib`.

### `scrapers/pcwatch/__init__.py`

- **Responsibility:** pcwatch-specific scraping logic.
- **Interfaces:**
  - `class PcwatchScraper(BaseScraper)` implementing:
    - `async def fetch_articles(source: Source, company: Company, date_range: DateRange) -> list[Article]`
    - `async def is_complete(source: Source, company: Company, date_range: DateRange) -> bool`
- **Dependencies:** Playwright, `src.models`, `src.storage`, `src.watchlist`, `scrapers.pcwatch.browser`.

### `scrapers/pcwatch/browser.py`

- **Responsibility:** Encapsulate Playwright browser lifecycle and page interactions for pcwatch.
- **Interfaces:**
  - `async def search_results(page: Page, term: str, stop_before: date) -> list[SearchResult]`
  - `async def extract_article(page: Page, url: str, bloomberg_ticker: str, source_id: str) -> Article`
- **Dependencies:** Playwright, `src.models`, `src.storage`.
- **Notes:** Runs headless by default. Headed mode can be enabled via an environment variable for debugging.

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
- `WatchlistEntry` (new):
  - `bloomberg_ticker`: `str`
  - `name`: `str`
  - `aliases`: `list[str]`
  - `search_terms`: `dict[str, list[str]]` — source ID to search terms.
  - `exhausted_before`: `dict[str, date]` — source ID to the date before which scraping was stopped.

Relationships:
- `WatchlistEntry` contains per-source search terms and exhaustion markers (1:N via dict keys).
- `Article` belongs to one `Source` (via `source_id`) and one `Company` (via `bloomberg_ticker`).

## API Design

### `list_sources()`

- **Returns:** `list[Source]`
- **Description:** Returns all sources loaded from `config.yaml`.

### `resolve_company(identifier: str)`

- **Parameters:** `identifier` — any company name or ticker.
- **Returns:** `Company`
- **Description:** Calls Gemini API to normalize the identifier to a Bloomberg ticker and updates the automatic watchlist.

### `research_company(bloomberg_ticker, question, start_date, end_date, sources)`

- **Parameters:**
  - `bloomberg_ticker`: `str` — canonical ticker.
  - `question`: `str` — analyst's question.
  - `start_date`: `str | None` — ISO date (`YYYY-MM-DD`), defaults to 6 months ago.
  - `end_date`: `str | None` — ISO date (`YYYY-MM-DD`), defaults to today.
  - `sources`: `list[str] | None` — optional source filter; defaults to all configured sources.
- **Returns:** `list[Article]`
- **Description:** Updates the watchlist, loads the requested scrapers, checks completeness, fetches missing articles, and returns merged results. The example source continues to return mock articles.

### Scraper Plugin Interface

Each scraper module exposes a class inheriting from `BaseScraper`:

```python
class BaseScraper(ABC):
    @abstractmethod
    async def fetch_articles(
        self,
        source: Source,
        company: Company,
        date_range: DateRange,
    ) -> list[Article]: ...

    @abstractmethod
    async def is_complete(
        self,
        source: Source,
        company: Company,
        date_range: DateRange,
    ) -> bool: ...
```

## Key Decisions

### Store raw Japanese content first; defer translation
- **Decision:** The pcwatch scraper stores only the original Japanese article text.
- **Rationale:** Reduces scope for the first scraper. Translation can be added later without changing storage paths or the `Article` model.
- **Trade-off:** Analysts must read Japanese or rely on external translation until translation is implemented.

### Use an automatic watchlist updated by tool calls
- **Decision:** Every successful `resolve_company` or `research_company` call updates `data/watchlist.yaml`.
- **Rationale:** Analysts never need to manually maintain a company list; the server learns from their queries. The watchlist also centralizes per-source search terms.
- **Trade-off:** The watchlist grows unbounded unless pruned later. It mixes analyst data with operational config.

### Deterministic title-hash paths for duplicate prevention
- **Decision:** Articles are stored at `data/{bloomberg_ticker}/{source_id}/{title_hash}.md` where `title_hash` is a truncated SHA-256 of the title.
- **Rationale:** Simple, no TTL logic needed. The same title always maps to the same file, so re-scraping is avoided.
- **Trade-off:** If an article title changes, a duplicate will be stored. If an article body is updated after first scrape, the cached version is stale.

### Multiple search terms per company
- **Decision:** The watchlist supports multiple search terms per source for a single company, and the scraper searches all of them.
- **Rationale:** Different sources and articles may use different names for the same company (e.g. "SK Hynix" vs "SK hynix"). Searching multiple terms improves coverage.
- **Trade-off:** More search terms mean more page loads. Deduplication by URL prevents duplicate articles.

### Playwright for browser automation
- **Decision:** Use Playwright to drive the browser for pcwatch.
- **Rationale:** pcwatch search results are rendered by Google Custom Search JavaScript, so static HTTP requests cannot extract result links reliably. Playwright is robust and was already used to explore the site.
- **Trade-off:** Adds a runtime dependency and increases resource usage per query.

### Abstract base class for scraper plugins
- **Decision:** Scrapers implement `BaseScraper` with `fetch_articles` and `is_complete`.
- **Rationale:** Provides a clear contract and consistent structure across source-specific scrapers.
- **Trade-off:** Slightly more boilerplate than module-level functions.

### Explicit `exhausted_before` marker for `is_complete`
- **Decision:** Store the date before which scraping stopped in the watchlist entry (`exhausted_before[source_id]`).
- **Rationale:** Correctly handles gaps in publication dates. The scraper can confidently say "we have everything in this range" when `DateRange.start >= exhausted_before`.
- **Trade-off:** Adds one field to `WatchlistEntry` and requires the scraper to update it after each fetch.

## Open Questions

- [ ] Should the scraper support a headless vs. headed mode toggle beyond an environment variable?
- [ ] How should rate limiting / politeness be enforced between page requests?
- [ ] Should the watchlist be pruned automatically after a certain number of entries?

## Risks & Mitigations

- **Risk:** Playwright browser startup is slow per query.
  - **Mitigation:** Reuse a single browser context within one `fetch_articles` call; optimize later if needed.
- **Risk:** Google Custom Search layout changes break selectors.
  - **Mitigation:** Keep selectors localized in `scrapers/pcwatch/browser.py`; add integration tests.
- **Risk:** Watchlist file grows unbounded.
  - **Mitigation:** Defer pruning; file size is not a concern for personal/local use.
- **Risk:** Playwright is a heavy dependency for users who only want the example/mock source.
  - **Mitigation:** Keep Playwright as an optional dependency group so users can install it only when they enable pcwatch.
