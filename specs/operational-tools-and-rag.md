# Spec: Operational Tools, Scraper Reliability & RAG

Last updated: 2026-07-14

## Summary

Add operational visibility/control tools and a lightweight RAG layer to the Investment Research MCP server. The `question` parameter in `research_company` becomes the basis for semantic retrieval, so analysts receive only the most relevant articles instead of every article in the date range. Also fix the pcwatch scraper’s exhaustion logic and add structured logging so silent failures and stale cache markers are easier to diagnose.

## User Roles

- **Investment Analyst (non-technical):** Uses natural language to research companies, ask why results look the way they do, and guide search behavior without editing config files.
- **Developer / Operator:** Curates sources via `config.yaml` and implements scrapers. Operational tools reduce support burden.

## User Stories

1. As an analyst, I want to see what the server knows about a company, so I understand why a research query returned empty.
   - Acceptance: `get_company_status` returns watchlist entry, search terms, exhaustion markers, and cached article counts per source.
2. As an analyst, I want to tell the server which search terms to use for a source, so it finds relevant articles in non-English sites.
   - Acceptance: `set_search_terms` updates terms for a company/source and clears the source’s exhaustion marker.
3. As an analyst, I want to force the server to re-scrape a source, so it picks up newly added articles or recovers from a bad cache state.
   - Acceptance: `reset_source_cache` clears the exhaustion marker and optionally deletes cached articles for a single source.
4. As an analyst, I want diagnostics before/after a research query, so the LLM can explain what happened.
   - Acceptance: `get_research_diagnostics` returns planned action, cache status, exhaustion status, and reason without scraping.
5. As an analyst, I want the server to rank articles by relevance to my question, so I am not overwhelmed by unrelated results as more sources are added.
   - Acceptance: `research_company` embeds the question and returns the top-K most relevant articles with relevance scores when `use_rag` is true.
6. As a developer, I want the scraper to only mark a date range as “exhausted” when it actually found articles in that range, so bad search terms do not poison future queries.
   - Acceptance: pcwatch only writes `exhausted_before` when at least one article is saved within the requested date range.

## Data Models

- `Company`: `{bloomberg_ticker, name, aliases[]}`
- `Source`: `{id, name, base_url, scraper_module, description}`
- `Article`: `{id, bloomberg_ticker, source_id, url, title, content, published_at, fetched_at, stored_path, relevance_score?}`
  - `relevance_score` is a float between 0.0 and 1.0 representing cosine similarity to the question embedding. Only populated when RAG is used.
- `CompanyStatus`: `{bloomberg_ticker, name, aliases[], sources: {source_id: {search_terms[], exhausted_before?, cached_article_count}}}`
- `ResearchDiagnostics`: `{bloomberg_ticker, source_id, date_range, search_terms[], exhausted_before?, is_complete, cached_article_count, planned_action, reason}`

## API Endpoints / MCP Tools

- `list_sources() -> Source[]` — show supported sources.
- `resolve_company(identifier: str) -> Company` — normalize any identifier to a Bloomberg ticker.
- `research_company(bloomberg_ticker, question?, start_date?, end_date?, sources?, use_rag?: bool = true, top_k?: int = 10) -> Article[]` — fetch/cache articles and return relevant raw articles inline. When `question` is provided and `use_rag` is true, embed the question and return the top-K most relevant articles sorted by cosine similarity.
- `get_company_status(bloomberg_tickers: str[]) -> CompanyStatus[]` — return watchlist metadata and per-source cache status for each requested ticker.
- `set_search_terms(bloomberg_ticker: str, source_id: str, terms: str[]) -> CompanyStatus` — update source-specific search terms and clear the source’s exhaustion marker.
- `reset_source_cache(bloomberg_ticker: str, source_id: str, delete_cached_articles: bool = false) -> CompanyStatus` — clear the exhaustion marker for a source and optionally delete its cached articles.
- `get_research_diagnostics(bloomberg_ticker: str, source_id?: str, start_date?: str, end_date?: str) -> ResearchDiagnostics` — report what `research_company` would do without scraping.

### `get_company_status` output example

```json
{
  "bloomberg_ticker": "000660 KS Equity",
  "name": "SK Hynix Inc.",
  "aliases": ["SK Hynix", "SK Hynix Inc.", "Hynix", "000660"],
  "sources": {
    "pcwatch": {
      "search_terms": ["SK Hynix"],
      "exhausted_before": "2024-07-11",
      "cached_article_count": 21
    },
    "example": {
      "search_terms": [],
      "exhausted_before": null,
      "cached_article_count": 3
    }
  }
}
```

### `get_research_diagnostics` output example

```json
{
  "bloomberg_ticker": "000660 KS Equity",
  "source_id": "pcwatch",
  "date_range": { "start": "2025-07-14", "end": "2026-07-14" },
  "search_terms": ["SK Hynix"],
  "exhausted_before": "2024-07-11",
  "is_complete": true,
  "cached_article_count": 0,
  "planned_action": "return_cached",
  "reason": "date_range.start (2025-07-14) >= exhausted_before (2024-07-11)"
}
```

Possible `planned_action` values:
- `return_cached` — cache covers the requested range.
- `scrape` — cache incomplete or missing; scraper will run.
- `skip_no_scraper` — source has no loadable scraper and is not the `example` source.
- `mock` — source is `example` and will return mock articles.

### `research_company` RAG output example

When RAG is used, each returned `Article` includes a `relevance_score`:

```json
{
  "id": "c378bad30ac640e4",
  "bloomberg_ticker": "000660 KS Equity",
  "source_id": "pcwatch",
  "url": "https://pc.watch.impress.co.jp/docs/news/2122927.html",
  "title": "SK hynix、米国上場で約4.5兆円調達。メモリなど生産能力拡大へ",
  "content": "...",
  "published_at": "2026-07-07T11:42:55+09:00",
  "fetched_at": "2026-07-14T...",
  "stored_path": "data/000660 KS Equity/pcwatch/c378bad30ac640e4.md",
  "relevance_score": 0.87
}
```

## RAG / Embeddings

### Embedding model

- **Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Reason:** Supports Japanese and English; good semantic similarity performance; small enough for local CPU.
- **Module:** `src/embeddings.py` loads the model lazily and exposes `embed(text: str) -> list[float]`.

### What to embed

- Article title + full content, concatenated.
- One embedding per article.
- Chunking deferred to a future iteration.

### Storage

- Embeddings stored in the existing article `.md` frontmatter.
- Brute-force cosine similarity at query time over the candidate articles.
- Vector database deferred until corpus scale justifies it.

### When to embed

- At scrape time, immediately after an article is saved.
- If an article lacks an embedding at query time, embed it on demand.

### Relevance scoring

- Return `relevance_score` (cosine similarity, 0.0–1.0) on each article when RAG is used.

## Scraper Fixes

### pcwatch exhaustion logic

**Current behavior:** `fetch_articles()` calls `set_exhausted_before(..., date_range.start)` unconditionally at the end.

**Desired behavior:** Only set the marker when the scraper actually found articles within the requested date range.

**Rule:** Set `exhausted_before` to `date_range.start` only if at least one article was saved within the range. If zero articles were found, do not write an exhaustion marker.

### Logging

Add structured log lines to stderr at `INFO`/`DEBUG` level for:

- Tool calls (`get_company_status`, `set_search_terms`, etc.)
- Scraper decisions (`is_complete` result, cache hit/miss, fallback to cache on error)
- Search terms being used per source
- Articles saved and their publish dates
- Exhaustion marker writes and clears

## Decisions

- **Use a local multilingual embedding model.**
  - Rationale: Avoids API cost and rate limits; supports Japanese pcwatch content and English analyst questions.
  - Trade-off: Adds a ~120MB model download and local CPU usage.

- **Embed article title + full content as a single vector.**
  - Rationale: Simpler than chunking and sufficient for news-length pcwatch articles.
  - Trade-off: Very long articles may dilute specific details; chunking is deferred.

- **Store embeddings in article `.md` frontmatter and use brute-force similarity search.**
  - Rationale: Keeps data in one place and avoids adding a vector database dependency for a small corpus.
  - Trade-off: Retrieval may slow down once the corpus grows past a few thousand articles; a vector DB migration may be needed later.

- **Embed articles at scrape time.**
  - Rationale: Keeps `research_company` fast; embedding happens once per article.
  - Trade-off: First scrape after enabling RAG is slower because each article is embedded.

- **RAG is opt-out per call with `use_rag` defaulting to true.**
  - Rationale: Encourages relevance filtering by default while preserving existing behavior when disabled.
  - Trade-off: Analysts may occasionally want all articles and must explicitly set `use_rag=false`.

- **`question` remains optional.**
  - Rationale: Preserves backward compatibility and supports “show me recent articles” style queries.
  - Trade-off: When no question is provided, results are not relevance-ranked.

- **Operational tools update state directly without confirmation prompts.**
  - Rationale: Changes are easily reversible with another tool call, so confirmation adds friction.
  - Trade-off: A misinterpreted LLM call could temporarily change search terms.

- **`set_search_terms` clears the exhaustion marker for the source.**
  - Rationale: New terms may find articles the old terms missed, so prior coverage is no longer trustworthy.
  - Trade-off: The next query rescrapes even if the old cache had useful articles.

- **`reset_source_cache` is source-specific and does not support `"all"`.**
  - Rationale: Search terms and cache state are source-dependent; a global reset is too blunt.
  - Trade-off: Resetting every source requires multiple calls.

- **Log to stderr only.**
  - Rationale: Simplest integration with MCP server processes and avoids log file management.
  - Trade-off: Logs are not persisted to disk.

- **Fix pcwatch exhaustion logic to only mark exhausted when articles are found in range.**
  - Rationale: Prevents bad search terms from writing a false marker that poisons future queries.
  - Trade-off: A successful but empty search (truly no articles) will rescrape on every overlapping query.

## Open Questions

- None.

## Constraints

- Python stack.
- Free tools preferred; local embedding model avoids API cost.
- No external vector database in the first iteration.
- Existing `.md` file storage format is preserved; embeddings are added to frontmatter.
