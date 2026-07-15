# Task 003: Backend - Embeddings Interface

## Description
Implement the lazy-loaded local embedding model interface in `src/embeddings.py`.

## Requirements
- Expose `embed(text: str) -> list[float]` and `is_available() -> bool`.
- Load `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` on the first call to `embed`.
- Log model load and embedding failures to stderr.
- Raise clear errors so callers can fall back to non-RAG behavior.

## Dependencies
- Blocks: [006, 007, 010, 013]
- Blocked by: [002]
- Parallelizable with: [004, 005]

## Success Criteria (5 points)
1. `embed("test")` returns a non-empty list of floats with consistent dimensionality.
2. `is_available()` returns `True` when the model loads and `False` when it fails.
3. The model is loaded on the first call to `embed`; subsequent calls reuse the cached instance.
4. Embedding failures are logged to stderr and re-raised with a descriptive message.
5. Importing `src.embeddings` does not trigger model download or load.

## Status
[003-backend-embeddings-status.md](../status/003-backend-embeddings-status.md)
