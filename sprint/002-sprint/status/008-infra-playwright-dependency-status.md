# Status: Task 008

## Progress
- Percentage: 100%
- State: Completed

## Notes / Blockers
- No blockers.

## Last Updated
2026-07-08

## Implementation Log
- Task created during sprint 002 decomposition.
- Added `[dependency-groups] scrapers` with `playwright>=1.40.0` to `pyproject.toml`.
- Regenerated `uv.lock` with `uv lock`.
- Updated CI to `uv sync --group dev --group scrapers`.
- Documented optional scraper install in `CLAUDE.md` and `README.md`.
- Verified `uv lock --locked` passes.
- Verified `uv sync --group scrapers` installs Playwright and the async API imports.
