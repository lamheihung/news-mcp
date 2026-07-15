# Task 010: Testing - Embeddings Interface

## Description
Write unit tests for the local embedding model interface in `src/embeddings.py`.

## Requirements
- Verify `embed` returns a float vector of the expected dimension.
- Verify `is_available` reflects model load success and failure.
- Verify lazy model loading behavior.
- Mock model load failures to cover error paths without requiring the full model.

## Dependencies
- Blocks: []
- Blocked by: [003]
- Parallelizable with: [011, 012]

## Success Criteria (5 points)
1. Tests pass when the real model is available.
2. Tests pass with a mocked model for failure scenarios.
3. `tests/test_embeddings.py` covers `embed`, `is_available`, and lazy loading.
4. Tests run in CI without requiring a GPU.
5. Test coverage for `src/embeddings.py` reaches at least 90%.

## Status
[010-testing-embeddings-status.md](../status/010-testing-embeddings-status.md)
