# Task 003: Infrastructure - Dependencies

## Description
Add the required runtime and development dependencies to `pyproject.toml` and regenerate the lockfile.

## Requirements
- Add `google-genai` for Gemini-based company identifier resolution.
- Add `pyyaml` for loading `config.yaml`.
- Add `pytest` and `pytest-asyncio` (or equivalent) for the testing tasks.
- Regenerate `uv.lock` so the environment is reproducible.
- Ensure all new imports resolve after running `uv sync`.

## Dependencies
- Blocks: [004, 005, 006, 007, 008]
- Blocked by: None
- Parallelizable with: [001, 002, 004]

## Success Criteria (5 points)
1. `pyproject.toml` lists `fastmcp`, `google-genai`, `pyyaml`, `pytest`, and `pytest-asyncio`.
2. `uv.lock` is regenerated and contains the new packages without conflicts.
3. `uv run python -c "import google.genai, yaml, fastmcp, pydantic"` succeeds.
4. `uv run pytest --version` executes successfully in the project environment.
5. `uv sync` completes with no dependency resolution errors.

## Status
[003-infra-dependencies-status.md](../status/003-infra-dependencies-status.md)
