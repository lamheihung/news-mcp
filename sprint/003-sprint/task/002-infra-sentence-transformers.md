# Task 002: Infrastructure - Sentence Transformers Dependency

## Description
Add the local multilingual embedding model dependency to the project so the RAG layer can run without external API calls.

## Requirements
- Add `sentence-transformers` to the appropriate dependency group in `pyproject.toml`.
- Regenerate `uv.lock` so it reflects the new dependency.
- Document the dependency size and model-download behavior in project guidance.
- Ensure CI resolves and installs the new dependency for test runs.

## Dependencies
- Blocks: [003]
- Blocked by: None
- Parallelizable with: [001]

## Success Criteria (5 points)
1. `pyproject.toml` includes `sentence-transformers` in a suitable dependency group.
2. `uv lock --locked` passes after the change.
3. `uv sync --group scrapers` installs the package and its transitive dependencies successfully.
4. `CLAUDE.md` or `README.md` notes the large model download and local CPU usage.
5. `.github/workflows/ci.yml` installs the dependency group needed for tests.

## Status
[002-infra-sentence-transformers-status.md](../status/002-infra-sentence-transformers-status.md)
