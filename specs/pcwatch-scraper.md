# Spec: pcwatch Scraper

Last updated: 2026-07-08

## Summary

A source-specific scraper plugin for `pcwatch` (`https://pc.watch.impress.co.jp/`) that integrates with the Investment Research MCP server. It searches the site for a company using source-specific search terms, collects matching articles in reverse-chronological order, stores them locally, and returns them as `Article` models for `research_company`. Raw Japanese content is stored; English translation is deferred to a later phase.

## User Roles

- **Investment Analyst (non-technical):** Uses natural language to ask research questions about a company on PC Watch. Never edits configuration files directly.
- **Developer / Operator:** Curates source registration in `config.yaml` and may seed or review search-term mappings in the automatic watchlist.

## User Stories

1. As an analyst, I want to research a company on PC Watch using natural language, so that I don't need to know the exact Japanese search term.
   - Acceptance: Saying "research SK Hynix in PCWatch" resolves the company, searches pcwatch, and returns relevant articles.

2. As an analyst, I want the server to remember companies I have researched, so that repeat queries are faster and search terms are reused.
   - Acceptance: The server maintains an automatic watchlist at `data/watchlist.yaml` and updates it when `resolve_company` or `research_company` succeeds.

3. As an analyst, I want the server to avoid re-scraping the same article, so that queries are fast and the site is not overloaded.
   - Acceptance: Articles are stored at deterministic paths based on title hash; existing files are read from disk instead of re-scraped.

4. As an analyst, I want sales and deal articles ignored, so that I only see research-relevant news.
   - Acceptance: Articles with `/docs/news/todays_sales/` in the URL are excluded.

5. As an analyst, I want articles limited to my requested date range, so that I can focus on recent or historical news.
   - Acceptance: The scraper stops paginating once search results are older than `DateRange.start`.

## Data Models

- `Company`: `{bloomberg_ticker, name, aliases[]}` — existing model from `resolve_company`.
- `Source`: `{id, name, base_url, scraper_module, description}` — registered in `config.yaml`.
- `Article`: `{id, bloomberg_ticker, source_id, url, title, content, published_at, fetched_at, stored_path}` — existing model.
- `WatchlistEntry`:
  - `bloomberg_ticker`: `str`
  - `name`: `str`
  - `aliases`: `list[str]`
  - `search_terms`: `dict[str, list[str]]` — mapping of source ID to list of search terms.

## API Endpoints / Scraper Interface

Each scraper module implements the plugin interface defined in `architecture/001-architecture-design.md`:

- `fetch_articles(source: Source, company: Company, date_range: DateRange) -> list[Article]`
  - Search pcwatch for the company using terms from the automatic watchlist.
  - Return articles published within `date_range`.
- `is_complete(source: Source, company: Company, date_range: DateRange) -> bool`
  - Return `True` when all locally cached articles cover the requested `date_range`.

## Configuration

### Source registration
`config.yaml` registers the source:
```yaml
sources:
  - id: pcwatch
    name: PC Watch
    base_url: https://pc.watch.impress.co.jp/
    scraper_module: scrapers.pcwatch
    description: Japanese PC/tech news site. Returns raw Japanese article content (English translation deferred).
```

### Automatic watchlist
`data/watchlist.yaml` is created and updated automatically:
```yaml
companies:
  - bloomberg_ticker: "000660 KS Equity"
    name: "SK hynix"
    aliases:
      - "SK Hynix"
      - "Hynix"
    search_terms:
      pcwatch:
        - "SK Hynix"
        - "SK hynix"
        - "Hynix"
```

- Updated on every successful `resolve_company` or `research_company` call.
- Search terms are source-specific and optional.
- If `search_terms.pcwatch` is missing, the scraper falls back to `Company.name`.

## Search Workflow

1. `research_company` invokes the pcwatch scraper with a `Company` and `DateRange`.
2. The scraper loads the watchlist entry for the company's ticker.
3. It resolves pcwatch search terms:
   - Use `search_terms.pcwatch` if present.
   - Otherwise fall back to `Company.name`.
4. For each search term, it opens the search URL sorted by newest date:
   ```
   https://pc.watch.impress.co.jp/extra/pcw/search/?q={term}&gsc.sort=date#gsc.tab=0&gsc.q={encoded_term}&gsc.page={N}&gsc.sort=date
   ```
5. It collects result URLs, titles, and snippet dates.
6. It skips URLs containing `/docs/news/todays_sales/`.
7. It stops paginating a term when the snippet date is older than `DateRange.start`.
8. It merges results from all terms, deduplicates by URL, and sorts by published date.
9. For each article not already cached, it opens the article page and extracts:
   - Title: `article h1`
   - Author: `article .article-info ul.author.list li` *(optional)*
   - Published datetime: `article .article-info .publish-date` (format: `2026年6月22日 06:06`)
   - Content: text inside `article .main-contents`, excluding `.related-links`/`.relatedLinks` and ad blocks
10. It saves each new article and returns `list[Article]`.

## Storage

- **Location:** `data/{bloomberg_ticker}/pcwatch/{title_hash}.md`
- **Title hash:** deterministic hash of the article title (e.g. SHA-256 truncated).
- **Duplicate prevention:** Before opening an article page, compute the title hash and check if the file exists. If it exists, read from disk and skip re-scraping.
- **File format:** Markdown with YAML frontmatter:
  ```yaml
  ---
  title: "高性能メモリHBM、冷却用“煙突”が必要になる時代に突入"
  url: "https://pc.watch.impress.co.jp/docs/column/tidbit/2118676.html"
  source: "pcwatch"
  published_at: "2026-06-22T06:06:00+09:00"
  fetched_at: "2026-07-08T10:00:00+09:00"
  bloomberg_ticker: "000660 KS Equity"
  ---
  {raw Japanese content}
  ```

## Date Handling

- Article-page datetime is authoritative.
- Search-result snippet date is a fallback (usually `YYYY/MM/DD`).
- Relative snippet dates (e.g. `7 日前`) fall back to the article-page datetime.

## Filtering

- Exclude URLs containing `/docs/news/todays_sales/`.
- Exclude articles whose published date is before `DateRange.start`.
- Stop paginating once results are older than `DateRange.start`.

## Decisions

### Store raw Japanese content first; defer translation
- **Rationale:** Reduces scope for the first scraper. Translation can be added later without changing storage paths or the `Article` model.
- **Trade-off:** Analysts must read Japanese or rely on external translation until Phase 2.

### Use an automatic watchlist updated by tool calls
- **Rationale:** Analysts never need to manually maintain a company list; the server learns from their queries. The watchlist also centralizes per-source search terms.
- **Trade-off:** The watchlist grows unbounded unless pruned later. It also mixes analyst data with operational config.

### Deterministic title-hash paths for duplicate prevention
- **Rationale:** Simple, no TTL logic needed. The same title always maps to the same file, so re-scraping is avoided.
- **Trade-off:** If an article title changes, a duplicate will be stored. If an article body is updated after first scrape, the cached version is stale.

### Multiple search terms per company
- **Rationale:** Different sources and articles may use different names for the same company (e.g. "SK Hynix" vs "SK hynix"). Searching multiple terms improves coverage.
- **Trade-off:** More search terms mean more page loads. Deduplication by URL prevents duplicate articles.

### Browser automation for Google Custom Search results
- **Rationale:** pcwatch search results are rendered by Google Custom Search JavaScript, so static HTTP requests cannot extract result links reliably.
- **Trade-off:** Adds a runtime dependency such as Playwright and increases resource usage per query.

## Open Questions

- [ ] Which browser automation library should be used? (e.g. Playwright, Selenium)
- [ ] Should the scraper support a headless vs. headed mode toggle for debugging?
- [ ] How should rate limiting / politeness be enforced between page requests?

## Constraints

- Python stack.
- Free tools only.
- Raw Japanese content stored; English translation deferred.
- Sources are developer-curated in `config.yaml`.
- Articles stored locally on the MCP server's filesystem.
- Default 6-month lookback when no date range is provided.
