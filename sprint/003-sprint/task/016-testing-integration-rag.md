# Task 016: Testing - Integration RAG and Operations

## Description
Update the end-to-end smoke test to exercise the new operational tools and RAG-enabled `research_company`.

## Requirements
- Add calls for `get_company_status`, `set_search_terms`, `reset_source_cache`, and `get_research_diagnostics`.
- Add a `research_company` call with `use_rag=true` and a question.
- Validate response shapes against `CompanyStatus` and `ResearchDiagnostics` models.
- Keep existing `list_sources`, `resolve_company`, and `research_company` checks.

## Dependencies
- Blocks: []
- Blocked by: [007, 009]
- Parallelizable with: [015]

## Success Criteria (5 points)
1. Integration test exercises all four new operational tools.
2. Integration test exercises `research_company` with `use_rag=true`.
3. Response JSON validates against the new Pydantic models.
4. Test gracefully skips live embedding when the model is unavailable.
5. Integration test passes end-to-end with the `example` source.

## Status
[016-testing-integration-rag-status.md](../status/016-testing-integration-rag-status.md)
