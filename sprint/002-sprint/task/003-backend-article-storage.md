# Task 003: Backend - Article Storage

## Description
Implement deterministic article cache paths and read/write/list helpers for locally stored articles.

## Requirements
- Implement `article_path(ticker, source_id, title) -> Path` using `data/{ticker}/{source_id}/{title_hash}.md`.
- Title hash must be deterministic (truncated SHA-256 to 16 hex characters).
- Implement `article_exists(ticker, source_id, title) -> bool`.
- Implement `save_article(article)` writing Markdown with YAML frontmatter.
- Implement `load_article(path) -> Article` parsing the frontmatter and content.
- Implement `list_cached_articles(ticker, source_id, date_range) -> list[Article]` filtered by `published_at`.

## Dependencies
- Blocks: [007, 009, 010, 011]
- Blocked by: None
- Parallelizable with: [001, 002, 004, 005]

## Success Criteria (5 points)
1. `article_path` returns a deterministic path ending in a 16-character hex hash.
2. `save_article` writes Markdown with YAML frontmatter and raw Japanese content.
3. `load_article` reconstructs an `Article` identical to the saved one.
4. `list_cached_articles` returns only articles whose `published_at` falls within `date_range`.
5. `article_exists` returns `True` after `save_article` and `False` before.

## Status
[003-backend-article-storage-status.md](../status/003-backend-article-storage-status.md)
