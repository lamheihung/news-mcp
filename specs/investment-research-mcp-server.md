# Spec: Investment Research MCP Server

Last updated: 2026-07-04

## Summary

An MCP server framework for investment analysts across any industry. Developers curate supported news/information sources as pluggable `scrapers/` modules. Analysts interact entirely through natural language in their LLM client. The server normalizes company identifiers to Bloomberg tickers, fetches and caches articles locally, and returns relevant raw articles inline for the LLM to synthesize into answers.

## User Roles

- **Investment Analyst (non-technical):** Uses natural language to ask research questions, optionally filtering by supported source or date range. Never edits config files or adds new sources.
- **Developer / Operator:** Curates supported sources by editing `config.yaml` and implementing source-specific scrapers in `scrapers/`.

## User Stories

1. As an analyst, I want to see which sources the server supports, so I know what I can ask about.
2. As an analyst, I want to research a company using any common identifier, so I don't need to know the exact ticker format.
3. As an analyst, I want to optionally limit my research to specific supported sources, so I can focus on trusted outlets.
4. As an analyst, I want to specify a date range for my question, so I can focus on recent or historical news. *(Default: last 6 months)*
5. As an analyst, I want the server to use cached articles when available and scrape only missing articles, so queries are fast and don't duplicate work.
6. As an analyst, I want the server to return relevant raw articles inline, so the LLM can answer in whatever format I asked for.
7. As an analyst, I want the LLM to answer based only on the configured sources, so I can trust the grounding.

## Data Models

- `Company`: `{bloomberg_ticker, name, aliases[]}`
- `Source`: `{id, name, base_url, scraper_module, description}`
- `Article`: `{id, bloomberg_ticker, source_id, url, title, content, published_at, fetched_at, stored_path}`

## API Endpoints / MCP Tools

- `list_sources() -> Source[]` — show the supported sources the analyst can use.
- `resolve_company(identifier: str) -> bloomberg_ticker` — normalize any identifier to a Bloomberg ticker via Gemini API.
- `research_company(bloomberg_ticker: str, question: str, date_range: DateRange, sources: str[]) -> Article[]` — fetch/cache articles and return relevant raw articles inline. `date_range` defaults to the last 6 months. `sources` defaults to all configured sources.

## Configuration

- `config.yaml` at the project root, edited by the developer/operator.
- Registers supported `Source`s and which `scraper_module` each uses.
- Configuration persists across server restarts.

## Storage

- **Location:** local filesystem of the MCP server process.
- **Path:** `data/{bloomberg_ticker}/{source_name}/{title_hash}.md`
- **File format:** Markdown with YAML frontmatter (`title`, `url`, `source`, `published_at`, `fetched_at`, `bloomberg_ticker`).
- **Duplicate prevention:** deterministic path based on title hash means the same article is never stored twice.

## Scraper Plugin Interface

Each source has a scraper module under `scrapers/` implementing:

- `fetch_articles(source: Source, company: Company, date_range: DateRange) -> Article[]`
- `is_complete(source: Source, company: Company, date_range: DateRange) -> bool`

## Error Handling

- If a scraper fails, the server returns whatever articles are already cached locally for the requested source, company, and date range.

## Decisions

- **Industry-agnostic** — applies to any sector, not just semiconductors.
- **Developer-curated sources** — each supported website has a custom scraper; analysts cannot add arbitrary sources.
- **Natural-language analyst interaction** — the LLM/host maps analyst requests to MCP tools.
- **Scrapers live in `scrapers/` package within the same repo.**
- **Articles stored locally on the MCP server's filesystem.**
- **Free tools only.**
- **Python implementation.**
- **Pluggable scrapers.**
- **Local `.md` file storage.**
- **Cache-aware retrieval.**
- **Default 6-month lookback.**
- **Ticker normalization via Gemini API free tier**, exposed as `resolve_company`.
- **Source-specific completeness** — each scraper decides how to ensure it has fetched all articles in the requested date range.
- **Publish date from article page.**
- **Raw articles returned inline** — the LLM synthesizes summaries, extracts facts, or quotes directly.
- **Focused single-purpose tools.**
- **Graceful scraper failures** — fall back to cached local articles.

## Open Questions

- [ ] Which website should be the first pilot scraper plugin? *(Deferred: build MCP server foundation first.)*

## Constraints

- Python stack.
- Free tools only.
