# Sprint 002 Overview

## Summary
- **Sprint Number:** 002
- **Total Tasks:** 15
- **Domains:** backend, infrastructure, testing
- **Estimated Duration:** 2-3 weeks

## Task Dependencies

### Dependency Graph
```
001 (backend-watchlist-model)
├── 002 (backend-watchlist-persistence)
│   ├── 006 (backend-resolver-watchlist)
│   │   └── 007 (backend-tools-orchestration)
│   │       ├── 014 (testing-tools-updates)
│   │       └── 015 (testing-integration-updates)
│   ├── 007 (backend-tools-orchestration)
│   └── 009 (backend-pcwatch-browser) [indirect: 002 not direct]
│       └── 010 (backend-pcwatch-scraper)
│           ├── 013 (testing-pcwatch)
│           ├── 014 (testing-tools-updates)
│           └── 015 (testing-integration-updates)
└── 009 (backend-pcwatch-browser)

003 (backend-article-storage)
└── 007 (backend-tools-orchestration)

004 (backend-scraper-base)
├── 005 (backend-scraper-loader)
│   └── 007 (backend-tools-orchestration)
└── 009 (backend-pcwatch-browser)

008 (infra-playwright-dependency)
└── 009 (backend-pcwatch-browser)

011 (testing-persistence)
012 (testing-scraper-loader)
013 (testing-pcwatch)
```

### Critical Path
The longest dependency chains determine the minimum sprint duration:
1. **Task 001** - Backend - Watchlist Model
2. **Task 002** - Backend - Watchlist Persistence
3. **Task 006** - Backend - Resolver Watchlist Update
4. **Task 007** - Backend - Tools Orchestration
5. **Task 015** - Testing - Integration Updates

An equivalent critical path runs through the scraper infrastructure:
1. **Task 001** - Backend - Watchlist Model
2. **Task 004** - Backend - Scraper Base Class
3. **Task 005** - Backend - Scraper Loader
4. **Task 007** - Backend - Tools Orchestration
5. **Task 015** - Testing - Integration Updates

### Dependency Matrix
| Task ID | Blocked By | Blocks | Parallelizable With |
|---------|------------|--------|---------------------|
| 001 | None | 002, 006, 009, 010 | 003, 004, 008 |
| 002 | 001 | 006, 007, 009, 010, 011 | 003, 004, 005 |
| 003 | None | 007, 009, 010, 011 | 001, 002, 004, 005 |
| 004 | None | 005, 009, 010, 012 | 001, 003, 008 |
| 005 | 004 | 007, 010, 012 | 002, 003 |
| 006 | 001, 002 | 007, 014, 015 | 003, 004, 005 |
| 007 | 002, 003, 005, 006 | 014, 015 | None |
| 008 | None | 009, 010, 013 | 001, 003, 004 |
| 009 | 001, 003, 004, 008 | 010, 013 | None |
| 010 | 001, 002, 003, 004, 005, 008, 009 | 013, 014, 015 | 006, 007 |
| 011 | 001, 002, 003 | None | 012 |
| 012 | 004, 005 | None | 011 |
| 013 | 008, 009, 010 | None | 014 |
| 014 | 006, 007 | None | 013, 015 |
| 015 | 007, 010 | None | 013, 014 |

## Tasks by Domain

### Backend
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 001 | Watchlist Model | Blocked by: None | Not Started |
| 002 | Watchlist Persistence | Blocked by: 001 | Not Started |
| 003 | Article Storage | Blocked by: None | Not Started |
| 004 | Scraper Base Class | Blocked by: None | Not Started |
| 005 | Scraper Loader | Blocked by: 004 | Not Started |
| 006 | Resolver Watchlist Update | Blocked by: 001, 002 | Not Started |
| 007 | Tools Orchestration | Blocked by: 002, 003, 005, 006 | Not Started |
| 009 | pcwatch Browser Helpers | Blocked by: 001, 003, 004, 008 | Not Started |
| 010 | pcwatch Scraper Plugin | Blocked by: 001, 002, 003, 004, 005, 008, 009 | Not Started |

### Infrastructure
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 008 | Playwright Dependency | Blocked by: None | Not Started |

### Testing
| ID | Task Name | Dependencies | Status |
|----|-----------|--------------|--------|
| 011 | Persistence Tests | Blocked by: 001, 002, 003 | Not Started |
| 012 | Scraper Loader Tests | Blocked by: 004, 005 | Not Started |
| 013 | pcwatch Scraper Tests | Blocked by: 008, 009, 010 | Not Started |
| 014 | Tools Tests Updates | Blocked by: 006, 007 | Not Started |
| 015 | Integration Tests Updates | Blocked by: 007, 010 | Not Started |

## Parallelization Opportunities

Tasks that can be worked on simultaneously:

**Group 1:** (can start immediately)
- Task 001 - Backend - Watchlist Model
- Task 003 - Backend - Article Storage
- Task 004 - Backend - Scraper Base Class
- Task 008 - Infrastructure - Playwright Dependency

**Group 2:** (starts once Group 1 foundations are in place)
- Task 002 - Backend - Watchlist Persistence
- Task 005 - Backend - Scraper Loader
- Task 009 - Backend - pcwatch Browser Helpers

**Group 3:** (starts once Group 2 is complete)
- Task 006 - Backend - Resolver Watchlist Update
- Task 010 - Backend - pcwatch Scraper Plugin

**Group 4:** (starts once Group 3 is complete)
- Task 007 - Backend - Tools Orchestration

**Group 5:** (starts once implementation tasks are complete)
- Task 011 - Testing - Persistence Tests
- Task 012 - Testing - Scraper Loader Tests
- Task 013 - Testing - pcwatch Scraper Tests
- Task 014 - Testing - Tools Tests Updates
- Task 015 - Testing - Integration Tests Updates

## Sprint Completion Criteria

All tasks in this sprint are complete when:
- [ ] All task success criteria verified
- [ ] All status files show "Done" state
- [ ] Unit test coverage is at least 80% across new `src/` and `scrapers/` modules
- [ ] Integration smoke test passes end-to-end
- [ ] `mypy src tests` passes
- [ ] `ruff check src tests` passes
- [ ] `uv lock --locked` passes
- [ ] No blocking issues remaining

## Notes
- This sprint implements the first real scraper (`pcwatch`) and the supporting watchlist/storage/scraper infrastructure described in `architecture/002-architecture-design.md` and `specs/pcwatch-scraper.md`.
- Playwright is intentionally kept as an optional dependency group so users who only need the example source are not forced to install browser binaries.
- The `example` source continues to return mock articles as a fallback until additional real scrapers are added.
- Translation of Japanese article content is deferred to a later phase; only raw Japanese content is stored.
