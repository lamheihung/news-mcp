# Investment Research MCP Server

An MCP server for investment analysts. Resolves company identifiers to Bloomberg tickers, fetches articles from developer-curated sources, and returns raw articles for LLM synthesis.

## Features

- **Company resolution** — normalize any common company name or ticker to a Bloomberg ticker via the Gemini API.
- **Automatic watchlist** — persist resolved companies to `data/watchlist.yaml`.
- **Developer-curated sources** — only sources listed in `config.yaml` can be queried.
- **Source scraper plugins** — pluggable scraper framework with a production `pcwatch` scraper for Japanese PC/tech news.
- **Article caching** — cached articles are stored under `data/{bloomberg_ticker}/{source_name}/{title_hash}.md`.

## Setup

1. Copy `.env.template` to `.env` and add your `GEMINI_API_KEY`.
2. Configure sources in `config.yaml`.
3. Install dependencies:
   ```bash
   uv sync
   ```
4. To enable source-specific scrapers (e.g. `pcwatch`), also install the optional group and Playwright:
   ```bash
   uv sync --group scrapers
   playwright install chromium
   ```
5. Run the server:
   ```bash
   uv run main.py
   ```

## Testing

```bash
uv run pytest tests
```

## Architecture

See `architecture/001-architecture-design.md`, `architecture/002-architecture-design.md`, and `specs/investment-research-mcp-server.md`.

For day-to-day development guidance, see `CLAUDE.md`.
