# Task 006: Backend - RAG Ranking

## Description
Implement article relevance ranking and on-demand embedding backfill in a dedicated `src/rag.py` module.

## Requirements
- Expose `ensure_embeddings(articles)` to backfill missing vectors by reading files and calling `embed`.
- Expose `rank_articles(question, articles, top_k)` that scores articles by cosine similarity to the question.
- Implement cosine similarity in pure Python without adding `numpy`.
- Fall back to unranked input articles when embedding is unavailable.

## Dependencies
- Blocks: [009, 013]
- Blocked by: [001, 003, 004]
- Parallelizable with: [005, 007, 008]

## Success Criteria (5 points)
1. `rank_articles` returns articles sorted by descending cosine similarity.
2. Each ranked article has a `relevance_score` between 0.0 and 1.0.
3. `ensure_embeddings` computes and persists missing vectors for articles loaded from storage.
4. When `embed` fails, `rank_articles` returns the input articles unchanged.
5. `top_k` limits the result count; passing `top_k >= len(articles)` returns all articles.

## Status
[006-backend-rag-status.md](../status/006-backend-rag-status.md)
