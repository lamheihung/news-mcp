# Task 009: Backend - Research Company RAG Integration

## Description
Integrate relevance ranking into `research_company` while keeping the existing behavior available when RAG is disabled.

## Requirements
- Add `use_rag: bool = true` and `top_k: int = 10` parameters.
- Embed the analyst's question and call `rank_articles` when `use_rag` is true and a question is provided.
- Preserve date-descending sort when RAG is disabled or no question is provided.
- Fall back to unranked results when embedding fails.

## Dependencies
- Blocks: [015, 016]
- Blocked by: [001, 004, 006, 008]
- Parallelizable with: None

## Success Criteria (5 points)
1. `research_company` accepts `use_rag` and `top_k` with the specified defaults.
2. With `use_rag=true` and a question, returned articles include `relevance_score` and are sorted by it.
3. With `use_rag=false`, results remain sorted by `published_at` descending.
4. With no question provided, RAG ranking is skipped and results are date sorted.
5. Embedding failures log an error and fall back to date-sorted unranked results.

## Status
[009-backend-research-rag-status.md](../status/009-backend-research-rag-status.md)
