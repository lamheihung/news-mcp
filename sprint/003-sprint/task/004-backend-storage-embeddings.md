# Task 004: Backend - Storage Embedding Round-Trip

## Description
Update article cache I/O to read and write embedding vectors from YAML frontmatter while remaining backward compatible with older files.

## Requirements
- Update `save_article` to persist an `embedding` field in frontmatter when present on the `Article`.
- Update `load_article` to populate the `Article` embedding from frontmatter when present.
- Preserve deterministic paths and existing frontmatter fields.
- Keep old articles without embeddings loadable and valid.

## Dependencies
- Blocks: [006, 007, 011]
- Blocked by: [001]
- Parallelizable with: [003, 005]

## Success Criteria (5 points)
1. `save_article` writes the `embedding` array to frontmatter when the article has one.
2. `load_article` reads the `embedding` array and returns it on the model.
3. Articles saved before this change load without errors and have no embedding.
4. A save-then-load round-trip preserves title, content, dates, and embedding vector.
5. `article_path` and path resolution remain unchanged.

## Status
[004-backend-storage-embeddings-status.md](../status/004-backend-storage-embeddings-status.md)
