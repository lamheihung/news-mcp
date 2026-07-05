# Structure v001

Created from: `architecture/001-architecture-design.md`

## Created

- `src/` package with placeholder modules:
  - `__init__.py`
  - `config.py`
  - `models.py`
  - `resolver.py`
  - `tools.py`
- `data/` directory for local article cache
- `config.yaml` for developer-curated sources
- `.env.template` for environment variables
- `structure/001-structure.md` (this file)

## Modified

- `main.py` — FastMCP entry point stub
- `.gitignore` — added data/ and .env ignores
- `README.md` — setup and usage overview

## Removed

- `server.py` — already absent; replaced by the new `src/` + `main.py` structure
