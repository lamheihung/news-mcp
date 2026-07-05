# Task 007: Testing - Unit Tests

## Description
Write unit tests for the data models, config loader, company resolver, and MCP tool handlers with all external dependencies mocked.

## Requirements
- Test valid and invalid `Company`, `Source`, `Article`, and `DateRange` instantiation.
- Test `load_config` with valid, empty, and invalid `config.yaml` content.
- Test `resolve_company` with mocked Gemini responses and missing API key scenarios.
- Test the three tool handlers using mocked config and resolver dependencies.
- Achieve at least 80% code coverage across `src/` modules.

## Dependencies
- Blocks: []
- Blocked by: [001, 002, 004, 005]
- Parallelizable with: [006, 008]

## Success Criteria (5 points)
1. `uv run pytest tests/` runs and all unit tests pass.
2. Coverage report shows `>= 80%` coverage for `src/models.py`, `src/config.py`, `src/resolver.py`, and `src/tools.py`.
3. Resolver tests cover both missing `GEMINI_API_KEY` and mocked success responses.
4. Tool handler tests verify `list_sources`, `resolve_company`, and `research_company` behavior.
5. No network requests are made during unit test execution.

## Status
[007-testing-unit-tests-status.md](../status/007-testing-unit-tests-status.md)
