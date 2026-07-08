# Task 011: Testing - Persistence Layer

## Description
Write unit tests for the watchlist and storage helpers using temporary paths.

## Requirements
- Test all public functions in `src/watchlist.py`.
- Test all public functions in `src/storage.py`.
- Use `tmp_path` fixtures and avoid writing to the real `data/` directory.
- Cover edge cases: empty watchlist, missing file, date boundaries, duplicate saves.
- Ensure tests run quickly and do not require Playwright.

## Dependencies
- Blocks: None
- Blocked by: [001, 002, 003]
- Parallelizable with: [012]

## Success Criteria (5 points)
1. All public functions in `watchlist.py` have test coverage.
2. All public functions in `storage.py` have test coverage.
3. Tests use temporary paths and leave the repository `data/` directory unchanged.
4. Edge cases are tested: empty watchlist, missing file, and date-range boundaries.
5. Coverage for `watchlist.py` and `storage.py` is at least 90%.

## Status
[011-testing-persistence-status.md](../status/011-testing-persistence-status.md)
