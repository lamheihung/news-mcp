# Task 001: Backend - Data Models

## Description
Define the Pydantic data models used across the MCP server: Company, Source, Article, and DateRange.

## Requirements
- Implement `Company`, `Source`, `Article`, and `DateRange` in `src/models.py`.
- Match field names and types specified in `architecture/001-architecture-design.md`.
- Support JSON/dict serialization and Pydantic validation.
- `DateRange` must enforce a valid start-to-end relationship.
- Models must import cleanly with no runtime errors.

## Dependencies
- Blocks: [002, 004, 005, 007]
- Blocked by: None
- Parallelizable with: [003]

## Success Criteria (5 points)
1. All four model classes exist in `src/models.py` and import without errors.
2. Pydantic rejects instantiation when required fields are missing or have wrong types.
3. `Article` serializes to a dict containing all nine fields defined in the architecture.
4. `DateRange` rejects an `end` date that is earlier than `start`.
5. Field names and types match `architecture/001-architecture-design.md` exactly.

## Status
[001-backend-data-models-status.md](../status/001-backend-data-models-status.md)
