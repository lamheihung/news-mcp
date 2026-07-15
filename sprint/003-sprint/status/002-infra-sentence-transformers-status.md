# Status: Task 002

## Progress
- Percentage: 100%
- State: Complete

## Notes / Blockers
- Task completed. Added `sentence-transformers` to the `scrapers` dependency group, regenerated `uv.lock`, updated project guidance, and verified CI installs the group.
- All pre-commit hooks pass.

## Last Updated
2026-07-15

## Implementation Log
- Added `sentence-transformers>=3.0.0` to `[dependency-groups] scrapers` in `pyproject.toml`.
- Regenerated `uv.lock` with `uv lock`.
- Installed successfully with `uv sync --group scrapers`.
- Updated `CLAUDE.md` and `README.md` to note the model download size and local CPU usage.
- CI already installs `--group scrapers`, so no workflow change was required.
