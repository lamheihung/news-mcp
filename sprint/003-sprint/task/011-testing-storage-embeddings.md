# Task 011: Testing - Storage Embedding Round-Trip

## Description
Write unit tests for the embedding frontmatter read/write behavior in `src/storage.py`.

## Requirements
- Test that `save_article` writes the embedding array to frontmatter.
- Test that `load_article` reads the embedding into the `Article` model.
- Test backward compatibility with articles that have no embedding.
- Test that date-range listing still works for embedded articles.

## Dependencies
- Blocks: []
- Blocked by: [004]
- Parallelizable with: [010, 012]

## Success Criteria (5 points)
1. A save-then-load round-trip preserves the embedding vector exactly.
2. An article without an embedding loads with `relevance_score=None` and no embedding.
3. `list_cached_articles` date-range filtering works for articles with embeddings.
4. Tests use temporary directories and do not pollute `data/`.
5. Test coverage for `src/storage.py` embedding paths reaches at least 90%.

## Status
[011-testing-storage-embeddings-status.md](../status/011-testing-storage-embeddings-status.md)
