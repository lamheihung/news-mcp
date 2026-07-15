# Task 013: Testing - RAG Ranking

## Description
Write unit tests for the relevance ranking and fallback behavior in `src/rag.py`.

## Requirements
- Test pure-Python cosine similarity computation.
- Test `rank_articles` sorting, `top_k` limiting, and `relevance_score` attachment.
- Test `ensure_embeddings` backfills missing vectors by reading files and calling `embed`.
- Test fallback when the embedding model is unavailable.

## Dependencies
- Blocks: []
- Blocked by: [006]
- Parallelizable with: [014]

## Success Criteria (5 points)
1. `rank_articles` returns articles sorted by descending cosine similarity.
2. `top_k` correctly limits the number of returned articles.
3. `ensure_embeddings` computes and persists missing vectors for cached articles.
4. Fallback path returns input articles unchanged when embedding fails.
5. Test coverage for `src/rag.py` reaches at least 90%.

## Status
[013-testing-rag-status.md](../status/013-testing-rag-status.md)
