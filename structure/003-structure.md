# Project Structure v003

Created: 2026-07-15
Based on: `architecture/003-architecture-design.md`

## Directory Tree

```
/Users/jonathanlam/opt/news-mcp/
├── main.py                     # FastMCP entry point (unchanged)
├── pyproject.toml              # uv project config (to be updated by /implement)
├── uv.lock                     # uv lock file (to be updated by /implement)
├── config.yaml                 # Developer-curated source registry (unchanged)
├── .env.template               # Environment variable template (unchanged)
├── .env                        # Local env file (gitignored, present locally)
├── .gitignore                  # Git ignore rules (unchanged)
├── .python-version             # Python version pin (unchanged)
├── .pre-commit-config.yaml     # Pre-commit hooks config (unchanged)
├── README.md                   # Project readme (unchanged)
├── CLAUDE.md                   # Claude Code project guidance (unchanged)
├── .mcp.json                   # MCP server local config
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline (unchanged)
├── src/                        # Core server package
│   ├── __init__.py
│   ├── config.py               # Source config loading (unchanged)
│   ├── models.py               # Pydantic models (to be updated)
│   ├── resolver.py             # Gemini ticker resolution (unchanged)
│   ├── tools.py                # MCP tool handlers (to be updated)
│   ├── watchlist.py            # Watchlist helpers (to be updated)
│   ├── storage.py              # Article cache I/O (to be updated)
│   ├── scraper_base.py         # BaseScraper interface (unchanged)
│   ├── scraper_loader.py       # Dynamic scraper loading (unchanged)
│   ├── embeddings.py           # NEW: local embedding model interface
│   └── rag.py                  # NEW: relevance ranking and backfill
├── scrapers/                   # Scraper plugins
│   ├── __init__.py
│   └── pcwatch/
│       ├── __init__.py         # PcwatchScraper (to be updated)
│       └── browser.py          # Playwright helpers (unchanged)
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_resolver.py
│   ├── test_tools.py           # To be updated
│   ├── test_watchlist.py       # To be updated
│   ├── test_storage.py         # To be updated
│   ├── test_scraper_loader.py
│   ├── test_main.py
│   ├── test_integration.py
│   ├── test_embeddings.py      # NEW
│   ├── test_rag.py             # NEW
│   └── test_scrapers/
│       ├── __init__.py
│       └── test_pcwatch.py     # To be updated
├── data/                       # Watchlist and cached articles
│   ├── watchlist.yaml
│   └── {bloomberg_ticker}/...  # Cached article markdown files
├── architecture/               # Architecture documents
│   ├── 001-architecture-design.md
│   ├── 002-architecture-design.md
│   └── 003-architecture-design.md
├── structure/                  # Versioned scaffold records
│   ├── 001-structure.md
│   ├── 002-structure.md
│   └── 003-structure.md        # This file
├── specs/                      # Product specifications
│   ├── investment-research-mcp-server.md
│   ├── pcwatch-scraper.md
│   └── operational-tools-and-rag.md
└── sprint/                     # Sprint documentation
    ├── 001-sprint/
    │   └── sprint-overview.md
    └── 002-sprint/
        └── sprint-overview.md
```

## Files Created

- `src/embeddings.py` — placeholder for the local sentence-transformer embedding interface (`embed`, `is_available`).
- `src/rag.py` — placeholder for relevance-ranking logic (`ensure_embeddings`, `rank_articles`) and pure-Python cosine similarity.
- `tests/test_embeddings.py` — placeholder for embedding module unit tests.
- `tests/test_rag.py` — placeholder for RAG ranking and fallback tests.
- `structure/003-structure.md` — this scaffold record.

## Files Modified (Implementation Deferred to /implement)

- `src/models.py` — add `SourceStatus`, `CompanyStatus`, `ResearchDiagnostics`, and `Article.relevance_score`.
- `src/storage.py` — read/write `embedding` from article `.md` frontmatter.
- `src/watchlist.py` — add `set_search_terms` and `clear_exhausted_before` helpers.
- `src/tools.py` — add `get_company_status`, `set_search_terms`, `reset_source_cache`, `get_research_diagnostics`; integrate `src/rag.rank_articles` into `research_company`.
- `scrapers/pcwatch/__init__.py` — only write `exhausted_before` when at least one article is saved in the requested date range.
- `tests/test_tools.py` — tests for new operational tools and RAG flow.
- `tests/test_watchlist.py` — tests for new watchlist helpers.
- `tests/test_storage.py` — tests for embedding frontmatter round-trip.
- `tests/test_scrapers/test_pcwatch.py` — tests for the exhaustion marker fix.

## Config Files

No new config files created in this scaffold. Existing config remains unchanged:

- `pyproject.toml` — uv project configuration. `/implement` will add `sentence-transformers` to the appropriate dependency group.
- `uv.lock` — uv lock file. `/implement` will regenerate after dependency changes.
- `config.yaml` — source registry (unchanged).
- `.env.template` — environment variable template (unchanged).
- `.pre-commit-config.yaml` — pre-commit hooks (unchanged).
- `.github/workflows/ci.yml` — CI pipeline (unchanged).

## Notes

- This is an upgrade scaffold; the project structure from v001 and v002 is preserved.
- Dependency selection and versioning for `sentence-transformers` are intentionally deferred to `/implement` per scaffold conventions.
- New placeholder modules contain no implementation code.
- Generated/ignored directories (`.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`) are omitted from the tree above.
