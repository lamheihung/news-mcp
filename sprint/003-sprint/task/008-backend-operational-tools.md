# Task 008: Backend - Operational Tools

## Description
Implement the four new MCP operational tools that inspect and mutate watchlist and cache state.

## Requirements
- Add `get_company_status(bloomberg_tickers)` returning a list of `CompanyStatus` objects.
- Add `set_search_terms(bloomberg_ticker, source_id, terms)` returning the updated `CompanyStatus`.
- Add `reset_source_cache(bloomberg_ticker, source_id, delete_cached_articles)` returning the updated `CompanyStatus`.
- Add `get_research_diagnostics(bloomberg_ticker, source_id?, start_date?, end_date?)` returning a list of `ResearchDiagnostics` objects.

## Dependencies
- Blocks: [009, 015]
- Blocked by: [001, 005]
- Parallelizable with: [006, 007]

## Success Criteria (5 points)
1. `get_company_status` returns per-source search terms, `exhausted_before`, and cached article counts.
2. `set_search_terms` updates the watchlist and clears the source's exhaustion marker.
3. `reset_source_cache` with `delete_cached_articles=true` removes the source's cached `.md` files.
4. `get_research_diagnostics` returns `planned_action` values from `{return_cached, scrape, skip_no_scraper, mock}` with a reason.
5. All four tools emit structured log lines to stderr.

## Status
[008-backend-operational-tools-status.md](../status/008-backend-operational-tools-status.md)
