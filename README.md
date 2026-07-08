# Investment Research MCP Server

An MCP server for investment analysts. Resolves company identifiers, fetches articles from curated sources, and returns raw articles for LLM synthesis.

## Setup

1. Copy `.env.template` to `.env` and add your `GEMINI_API_KEY`.
2. Configure sources in `config.yaml`.
3. Install dependencies:
   ```bash
   uv sync
   ```
   To enable source-specific scrapers (e.g. pcwatch), also install the optional group:
   ```bash
   uv sync --group scrapers
   ```
4. Run the server:
   ```bash
   uv run main.py
   ```

## Architecture

See `architecture/001-architecture-design.md`, `architecture/002-architecture-design.md`, and `specs/investment-research-mcp-server.md`.
