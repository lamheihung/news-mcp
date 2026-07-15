# Task 015: Testing - Operational Tools and RAG Flow

## Description
Update `tests/test_tools.py` to cover the new operational tools and the RAG-aware `research_company` flow.

## Requirements
- Add tests for `get_company_status`, `set_search_terms`, `reset_source_cache`, and `get_research_diagnostics`.
- Add tests for `research_company` with `use_rag=true/false` and with/without a question.
- Verify operational tool logging output.
- Use temporary watchlist and storage paths to keep tests isolated.

## Dependencies
- Blocks: []
- Blocked by: [008, 009]
- Parallelizable with: [016]

## Success Criteria (5 points)
1. All four operational tools have passing unit tests with valid and invalid inputs.
2. `research_company` with `use_rag=true` returns articles with `relevance_score` when a question is given.
3. `research_company` with `use_rag=false` returns articles sorted by `published_at` descending.
4. Operational tool tests verify watchlist and cache mutations.
5. Test coverage for `src/tools.py` remains at least 80%.

## Status
[015-testing-tools-operational-status.md](../status/015-testing-tools-operational-status.md)
