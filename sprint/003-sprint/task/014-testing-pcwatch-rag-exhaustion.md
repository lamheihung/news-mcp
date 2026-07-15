# Task 014: Testing - pcwatch RAG and Exhaustion

## Description
Write unit and integration tests for the pcwatch scraper's scrape-time embedding and exhaustion-marker fix.

## Requirements
- Test that the exhaustion marker is written only when articles are found in range.
- Test that saved articles contain an embedding vector.
- Test structured log output from the scraper.
- Update existing `tests/test_scrapers/test_pcwatch.py` to cover the new behavior.

## Dependencies
- Blocks: []
- Blocked by: [007]
- Parallelizable with: [013]

## Success Criteria (5 points)
1. Unit test confirms no exhaustion marker is written for empty scrape results.
2. Unit test confirms exhaustion marker is written when articles are saved.
3. Saved articles in tests contain an `embedding` field in frontmatter.
4. Structured log messages are captured and verified.
5. Existing pcwatch integration tests continue to pass.

## Status
[014-testing-pcwatch-rag-exhaustion-status.md](../status/014-testing-pcwatch-rag-exhaustion-status.md)
