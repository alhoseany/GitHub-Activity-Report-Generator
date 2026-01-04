# GitHub Activity Report Generator - Project Memory

> **Purpose**: This file maintains project context across AI agent sessions. Read this first when starting a session. Update when making significant progress or ending a session.

---

## Quick Start for AI Agents

1. **Read this file first** to understand project status
2. **Follow implement.md** for step-by-step implementation
3. **Check tasks-by-usecase.md** for acceptance criteria
4. **Reference plan-v2.md** for detailed specifications
5. **Update this file** when you make progress or end session

---

## Project Overview

**Goal**: Build a CLI tool that generates GitHub activity reports (monthly/quarterly) for a user, outputting JSON and Markdown files.

**Tech Stack**: Python 3.11+, Click CLI, PyYAML, jsonschema, rich

**Key Features**:
- Adaptive fetching (week-by-week, day fallback for high activity)
- Multiple output formats (JSON, Markdown)
- Configurable metrics and filtering
- Automatic log and report cleanup
- Caching for API responses

---

## Document Map

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `MEMORY.md` | Project context & progress | Start/end of session |
| `implement.md` | Step-by-step code guide | Primary implementation reference |
| `tasks-by-usecase.md` | Specs & acceptance criteria | Verify task completion |
| `plan-v2.md` | Full specifications | Detailed reference |
| `tasks.md` | Technical task breakdown | Cross-reference TASK-X.Y IDs |

---

## Current Status

### Overall Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Core Setup | 🟢 Complete | Directory structure, dependencies |
| Phase 2: Basic Functionality | 🟢 Complete | CLI, fetchers, reporters, orchestrator |
| Phase 3: Period & Filtering | 🟢 Complete | Period selection, user/repo filters |
| Phase 4: Customization | 🟢 Complete | Output, metrics, caching config |
| Phase 5: Operations | 🟢 Complete | Logging, log cleanup, report cleanup |
| Phase 6: Quality | 🟡 In Progress | Schema validation complete, tests pending |

**Legend**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete

### Current Task

**Maintenance** - Implementation complete, documentation updated.

### Blockers

None currently.

---

## Implementation Checklist

### Phase 1: Core Setup
- [x] UC-1.1: Create project structure
- [x] UC-1.2: Install dependencies (requirements.txt, pytest.ini)

### Phase 2: Basic Functionality
- [x] UC-2.1: Create CLI entry point (generate_report.py)
- [x] UC-2.2: Implement fetchers (events, commits, PRs, issues, reviews, comments)
- [x] UC-2.3: Implement data aggregator
- [x] UC-2.4: Implement reporters (JSON, Markdown)
- [x] UC-2.5: Implement orchestrator (full pipeline)

### Phase 3: Period & Filtering
- [x] UC-3.1: Period selection (-m, -q, -y)
- [x] UC-4.1: User/org configuration
- [x] UC-5.1: Repository filters (include/exclude with wildcards)

### Phase 4: Customization
- [x] UC-6.1: Output settings (formats, include_links, commit_message_format)
- [x] UC-7.1: Metrics configuration (PR, review, engagement, productivity)
- [x] UC-8.1: Caching configuration (TTL, directory)

### Phase 5: Operations
- [x] UC-9.1: Logging configuration (Rich console, JSONL file)
- [x] UC-10.1: Log cleanup (retention, rotation)
- [x] UC-11.1: Report cleanup (versions, archival)

### Phase 6: Quality
- [x] UC-12.1: Schema validation
- [ ] UC-13.1: Unit tests
- [ ] UC-13.2: Integration tests

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI Framework | Click | Simple, widely used, good defaults |
| Config Priority | CLI > ENV > YAML > Defaults | Standard precedence |
| Fetching Strategy | Adaptive week/day | Handle high-activity periods |
| Log Rotation | No symlinks | Cross-platform compatibility |
| Report Versioning | Increment suffix (-1, -2, -3) | Keep multiple versions per period |

---

## Important Defaults

| Setting | Default | Plan Section |
|---------|---------|--------------|
| `high_activity_threshold` | 100 | 3.4 |
| `request_delay` | 1.0s | 3.4 |
| `cache.ttl_hours` | 24 | 3.5 |
| `output.formats` | ["json", "markdown"] | 3.6 |
| `include_private` | true | 3.3 |
| `include_forks` | false | 3.3 |
| `logging.level` | INFO | 3.8 |
| `cleanup.retention_days` | 30 | 3.9 |
| `cleanup.keep_versions` | 3 | 3.10 |

---

## File Structure (Current)

```
.scripts/github-activity/
├── generate_report.py          # CLI entry point
├── config.yaml                 # User configuration
├── requirements.txt            # Dependencies
├── pytest.ini                  # Test configuration
├── src/
│   ├── __init__.py
│   ├── orchestrator.py         # Main pipeline
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py           # YAML config loading
│   │   ├── settings.py         # Dataclasses
│   │   └── schema.json         # JSON schema
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseFetcher with adaptive strategy
│   │   ├── events.py           # User events (90-day limit)
│   │   ├── commits.py          # Commit search
│   │   ├── pull_requests.py    # PRs with details, reviewed PRs
│   │   ├── issues.py           # Issue search
│   │   ├── reviews.py          # PR reviews (given and received)
│   │   └── comments.py         # Issue + review comments
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── aggregator.py       # Data aggregation and filtering
│   │   └── metrics.py          # Advanced metrics calculation
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   ├── markdown_report.py
│   │   └── validator.py
│   └── utils/
│       ├── __init__.py
│       ├── gh_client.py        # GitHub CLI wrapper
│       ├── cache.py            # Response caching with TTL
│       ├── file_utils.py       # File operations
│       ├── date_utils.py       # Date utilities
│       ├── repo_filter.py      # Repository whitelist/blacklist
│       ├── logger.py           # Rich console + JSONL file logging
│       ├── log_cleanup.py      # Log rotation and cleanup
│       └── report_cleanup.py   # Report versioning and cleanup
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── api_responses/      # Mock API response data
│   │   └── expected_outputs/   # Expected report outputs
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── reports/
│   └── {year}/
│       └── {username}/         # Reports grouped by user
├── logs/
│   └── errors/
├── .cache/
└── docs/
    ├── MEMORY.md               # This file
    ├── implement.md            # Implementation guide
    ├── tasks-by-usecase.md     # Use case tasks
    ├── tasks.md                # Technical tasks
    ├── plan-v2.md              # Full specification
    └── plan.md                 # Original plan
```

---

## Progress Log

### 2026-01-04 - Documentation Consistency Update

**Session Summary**:
- Updated plan.md to match actual implementation
- Updated MEMORY.md with current status
- Fixed directory structure docs (reports now grouped by user)
- Fixed CLI options documentation
- Fixed module structure documentation

**Changes Made**:
- Reports directory: `reports/{year}/{username}/` (grouped by user)
- Added `comments.py` fetcher (issue + review comments)
- Added `cache.py`, `repo_filter.py`, `loader.py` to docs
- Removed documented but unimplemented: `repositories.py`, `filters.py`
- CLI: `-o` is `--output-dir` (not `--orgs`), `--log-level` (not `-v`)
- CLI: Added `--include-repos`, `--exclude-repos`, `-c/--config`, `--dry-run`

### 2026-01-03 - Implementation Complete

**Session Summary**:
- Completed all implementation phases (1-5)
- Generated reports for Q4 2025
- Fixed metrics calculations (PR commits, review turnaround)
- Added comments fetcher for complete comment data
- Added user-based report organization

### 2026-01-03 - Project Planning Complete

**Session Summary**:
- Created comprehensive plan (plan-v2.md) with Specification-Implementation pattern
- Created tasks-by-usecase.md organizing 13 use cases
- Created implement.md with step-by-step code guide
- Created this MEMORY.md file
- Verified consistency across all documents

**Documents Created**:
- `plan-v2.md` - Full specifications
- `tasks-by-usecase.md` - Use case organized tasks
- `tasks.md` - Technical task breakdown
- `implement.md` - Implementation guide
- `MEMORY.md` - This file

---

## Session Notes Template

When ending a session, copy this template and fill in:

```markdown
### YYYY-MM-DD - [Brief Description]

**Session Summary**:
- [What was accomplished]
- [Any issues encountered]
- [Decisions made]

**Tasks Completed**:
- [ ] UC-X.Y: [Task name]

**Current State**:
- Working on: [Current task]
- Blocked by: [Any blockers]

**Next Steps**:
1. [Next task]
2. [Following task]
```

---

## Reminders for AI Agents

1. **Code Markers**: Tag all code with `# UC-X.Y | PLAN-X.X`
2. **Verify Acceptance Criteria**: Check tasks-by-usecase.md after each task
3. **Update This File**: Log progress before ending session
4. **No Over-Engineering**: Implement only what's specified
5. **Test As You Go**: Verify each component works
6. **Use implement.md**: Follow the step-by-step guide for code

---

*Last Updated: 2026-01-04*
*Last Session: Documentation consistency update, implementation complete*
