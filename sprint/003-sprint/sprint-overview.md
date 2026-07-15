# Sprint 003 Overview

## Summary
- **Sprint Number:** 003
- **Total Tasks:** 16
- **Domains:** backend, infrastructure, testing
- **Estimated Duration:** 2-3 weeks
- **Status:** Not Started

## Task Dependencies

### Dependency Graph
```
001 (backend-models-update)
├── 004 (backend-storage-embeddings)
│   ├── 006 (backend-rag)
│   │   └── 009 (backend-research-rag)
│   │       ├── 015 (testing-tools-operational)
│   │       └── 016 (testing-integration-rag)
│   └── 007 (backend-pcwatch-rag-exhaustion)
│       ├── 009 (backend-research-rag) [indirect: via tools.py sequence]
│       ├── 014 (testing-pcwatch-rag-exhaustion)
│       └── 016 (testing-integration-rag)
└── 005 (backend-watchlist-ops)
    ├── 007 (backend-pcwatch-rag-exhaustion)
    ├── 008 (backend-operational-tools)
    │   ├── 009 (backend-research-rag)
    │   └── 015 (testing-tools-operational)
    └── 012 (testing-watchlist-ops)

002 (infra-sentence-transformers)
└── 003 (backend-embeddings)
    ├── 006 (backend-rag)
    ├── 007 (backend-pcwatch-rag-exhaustion)
    └── 010 (testing-embeddings)

010 (testing-embeddings)
011 (testing-storage-embeddings)
012 (testing-watchlist-ops)
013 (testing-rag)
014 (testing-pcwatch-rag-exhaustion)
015 (testing-tools-operational)
016 (testing-integration-rag)
```

### Critical Path
The longest dependency chains determine the minimum sprint duration:

1. **Task 001** - Backend - Models Update
2. **Task 004** - Backend - Storage Embedding Round-Trip
3. **Task 006** - Backend - RAG Ranking
4. **Task 009** - Backend - Research Company RAG Integration
5. **Task 016** - Testing - Integration RAG and Operations

An equivalent path runs through operational tools:
1. **Task 001** - Backend - Models Update
2. **Task 005** - Backend - Watchlist Operational Helpers
3. **Task 008** - Backend - Operational Tools
4. **Task 009** - Backend - Research Company RAG Integration
5. **Task 016** - Testing - Integration RAG and Operations

The embedding infrastructure path feeds into Task 006:
1. **Task 002** - Infrastructure - Sentence Transformers Dependency
2. **Task 003** - Backend - Embeddings Interface
3. **Task 006** - Backend - RAG Ranking

### Dependency Matrix
| Task ID | Blocked By | Blocks | Parallelizable With |
|---------|------------|--------|---------------------|
| 001 | None | 004, 005, 006, 007, 008, 009, 011, 012, 013, 015 | 002 |
| 002 | None | 003 | 001 |
| 003 | 002 | 006, 007, 010 | 004, 005 |
| 004 | 001 | 006, 007, 011 | 003, 005 |
| 005 | 001 | 007, 008, 012 | 003, 004 |
| 006 | 001, 003, 004 | 009, 013 | 005, 007, 008 |
| 007 | 001, 003, 004, 005 | 009, 014, 016 | 006, 008 |
| 008 | 001, 005 | 009, 015 | 006, 007 |
| 009 | 001, 004, 006, 008 | 015, 016 | None |
| 010 | 003 | None | 011, 012 |
| 011 | 004 | None | 010, 012 |
| 012 | 005 | None | 010, 011 |
| 013 | 006 | None | 014 |
| 014 | 007 | None | 013 |
| 015 | 008, 009 | None | 016 |
| 016 | 007, 009 | None | 015 |

## Tasks by Domain

### Backend
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 001 | Models Update | Blocked by: None | Not Started |
| 003 | Embeddings Interface | Blocked by: 002 | Not Started |
| 004 | Storage Embedding Round-Trip | Blocked by: 001 | Not Started |
| 005 | Watchlist Operational Helpers | Blocked by: 001 | Not Started |
| 006 | RAG Ranking | Blocked by: 001, 003, 004 | Not Started |
| 007 | pcwatch RAG and Exhaustion Fix | Blocked by: 001, 003, 004, 005 | Not Started |
| 008 | Operational Tools | Blocked by: 001, 005 | Not Started |
| 009 | Research Company RAG Integration | Blocked by: 001, 004, 006, 008 | Not Started |

### Infrastructure
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 002 | Sentence Transformers Dependency | Blocked by: None | Not Started |

### Testing
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 010 | Embeddings Interface Tests | Blocked by: 003 | Not Started |
| 011 | Storage Embedding Round-Trip Tests | Blocked by: 004 | Not Started |
| 012 | Watchlist Operational Helpers Tests | Blocked by: 005 | Not Started |
| 013 | RAG Ranking Tests | Blocked by: 006 | Not Started |
| 014 | pcwatch RAG and Exhaustion Tests | Blocked by: 007 | Not Started |
| 015 | Operational Tools and RAG Flow Tests | Blocked by: 008, 009 | Not Started |
| 016 | Integration RAG and Operations Tests | Blocked by: 007, 009 | Not Started |

## Parallelization Opportunities

Tasks that can be worked on simultaneously:

**Group 1:** (can start immediately)
- Task 001 - Backend - Models Update
- Task 002 - Infrastructure - Sentence Transformers Dependency

**Group 2:** (starts once Group 1 foundations are in place)
- Task 003 - Backend - Embeddings Interface
- Task 004 - Backend - Storage Embedding Round-Trip
- Task 005 - Backend - Watchlist Operational Helpers

**Group 3:** (starts once Group 2 is complete)
- Task 006 - Backend - RAG Ranking
- Task 007 - Backend - pcwatch RAG and Exhaustion Fix
- Task 008 - Backend - Operational Tools

**Group 4:** (starts once Group 3 is complete)
- Task 009 - Backend - Research Company RAG Integration

**Group 5:** (starts once embedding/storage/watchlist implementations are complete)
- Task 010 - Testing - Embeddings Interface Tests
- Task 011 - Testing - Storage Embedding Round-Trip Tests
- Task 012 - Testing - Watchlist Operational Helpers Tests
- Task 013 - Testing - RAG Ranking Tests
- Task 014 - Testing - pcwatch RAG and Exhaustion Tests

**Group 6:** (starts once all implementation is complete)
- Task 015 - Testing - Operational Tools and RAG Flow Tests
- Task 016 - Testing - Integration RAG and Operations Tests

## Sprint Completion Criteria

All tasks in this sprint are complete when:
- [ ] All task success criteria verified
- [ ] All status files show "Done" state
- [ ] Unit test coverage is at least 80% across new `src/` and `scrapers/` modules
- [ ] Integration smoke test passes end-to-end
- [ ] `mypy src tests` passes
- [ ] `ruff check src tests` passes
- [ ] `ruff format --check src tests` passes
- [ ] `uv lock --locked` passes
- [ ] No blocking issues remaining

## Notes
- This sprint implements the RAG layer and operational tools described in `architecture/003-architecture-design.md` and `specs/operational-tools-and-rag.md`.
- `sentence-transformers` is intentionally added as a dependency because the spec requires a local multilingual embedding model; document the size and cold-start cost in project guidance.
- `src/tools.py` is updated in two sequential tasks (008 and 009) to avoid file-conflicts between the four new operational tools and the `research_company` RAG integration.
- The pcwatch scraper gains both scrape-time embedding and the exhaustion-marker fix in a single task because both changes live in `scrapers/pcwatch/__init__.py`.
- Logging is added to stderr only, per the architecture decision; no log files are introduced.
