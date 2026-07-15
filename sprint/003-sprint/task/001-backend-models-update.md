# Task 001: Backend - Models Update

## Description
Extend the Pydantic models in `src/models.py` to support RAG relevance scores and the new operational-tool return types.

## Requirements
- Add an optional `relevance_score` field to `Article`.
- Add `SourceStatus`, `CompanyStatus`, and `ResearchDiagnostics` models per the architecture spec.
- Ensure new models serialize cleanly with `model_dump(mode="json")` for MCP tool responses.
- Keep `DateRange`, `Company`, `Source`, and `WatchlistEntry` unchanged except where required.

## Dependencies
- Blocks: [004, 005, 006, 007, 008, 009, 011, 012, 013, 015]
- Blocked by: None
- Parallelizable with: [002]

## Success Criteria (5 points)
1. `Article` accepts an optional `relevance_score` constrained to the range 0.0–1.0.
2. `SourceStatus`, `CompanyStatus`, and `ResearchDiagnostics` validate all required fields from the spec.
3. `model_dump(mode="json")` output matches the spec example shapes for `CompanyStatus` and `ResearchDiagnostics`.
4. Existing model tests in `tests/test_models.py` continue to pass.
5. New models are importable from `src.models` without circular imports.

## Status
[001-backend-models-update-status.md](../status/001-backend-models-update-status.md)
