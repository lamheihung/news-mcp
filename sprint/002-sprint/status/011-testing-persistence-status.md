# Status: Task 011

## Progress
- Percentage: 100%
- State: Completed

## Notes / Blockers
- No blockers.

## Last Updated
2026-07-10

## Implementation Log
- Created `tests/test_watchlist.py` covering all public functions:
  - `load_watchlist`: missing file creation, valid load, empty file, missing/null companies, validation error
  - `save_watchlist`: YAML output, parent directory creation, round-trip, atomic write cleanup
  - `upsert_company`: new entry, update preserving terms/markers, alias copy behavior
  - `get_search_terms`, `get_exhausted_before`: known/missing ticker/source cases
  - `set_exhausted_before`: set, overwrite, missing ticker error
- Created `tests/test_storage.py` covering all public functions:
  - `_title_hash` / `article_path`: determinism, hash format, path structure
  - `article_exists`: present/missing file cases
  - `save_article`: directory creation, YAML frontmatter, custom stored_path
  - `load_article`: round-trip, missing frontmatter, content without trailing newline
  - `list_cached_articles`: missing directory, date-range inclusion/exclusion, descending sort, start==end
- All tests use `tmp_path` fixtures and never touch the real `data/` directory.
- Coverage for `src/watchlist.py` and `src/storage.py`: 100%.
- Quality gates pass: pytest (104 passed, 1 skipped), ruff lint/format, mypy, bandit.
