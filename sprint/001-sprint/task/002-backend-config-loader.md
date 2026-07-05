# Task 002: Backend - Config Loader

## Description
Load and validate the developer-curated source registry from `config.yaml` into `Source` Pydantic models.

## Requirements
- Implement `load_config(path: Path) -> list[Source]` in `src/config.py`.
- Validate every source against the `Source` model and fail fast with readable errors.
- Support an empty `sources` list without crashing.
- Provide a documented example source in `config.yaml` so the server can start and be tested.
- Treat a missing or malformed `config.yaml` as a startup-blocking error with a clear message.

## Dependencies
- Blocks: [005, 006, 007, 008]
- Blocked by: [001]
- Parallelizable with: [003, 004]

## Success Criteria (5 points)
1. `load_config("config.yaml")` returns a list of `Source` Pydantic models when invoked.
2. A missing or malformed `config.yaml` raises a clear, readable error at load time.
3. A source entry missing any required field (`id`, `name`, `base_url`, `scraper_module`) is rejected with a Pydantic validation error.
4. `config.yaml` contains a documented example source entry matching the `Source` model.
5. An empty `sources` list in `config.yaml` loads as an empty list without errors.

## Status
[002-backend-config-loader-status.md](../status/002-backend-config-loader-status.md)
