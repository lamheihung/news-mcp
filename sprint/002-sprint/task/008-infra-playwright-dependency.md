# Task 008: Infrastructure - Playwright Dependency

## Description
Add Playwright as an optional dependency group so users who enable the pcwatch scraper can install browser automation libraries separately.

## Requirements
- Add a `scrapers` dependency group in `pyproject.toml` containing `playwright` and any required testing extras.
- Update `uv.lock` so the group is installable.
- Update CI to install the `scrapers` group when running pcwatch-related tests.
- Document the optional install in `CLAUDE.md` or README.
- Keep Playwright out of the default dependency set.

## Dependencies
- Blocks: [009, 010, 013]
- Blocked by: None
- Parallelizable with: [001, 003, 004]

## Success Criteria (5 points)
1. `pyproject.toml` contains a `scrapers` dependency group with `playwright`.
2. `uv sync --group scrapers` installs Playwright successfully.
3. CI workflow installs the `scrapers` group for pcwatch tests.
4. README or `CLAUDE.md` documents how to install optional scraper dependencies.
5. `uv lock --locked` passes after the change.

## Status
[008-infra-playwright-dependency-status.md](../status/008-infra-playwright-dependency-status.md)
