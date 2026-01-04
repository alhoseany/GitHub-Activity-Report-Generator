# GitHub Activity Report Generator - Implementation Tasks

> **Traceability Document** linking Plan -> Tasks -> Code
>
> Each task includes all information needed for autonomous implementation.

---

## Traceability System

### How It Works

```
+-------------+     +-------------+     +-------------+
|  plan-v2.md |---->|  tasks.md   |---->|  Code Files |
|  Section X  |     |  TASK-X.Y   |     |  # TASK-X.Y |
+-------------+     +-------------+     +-------------+
       |                   |                   |
       +-------------------+-------------------+
                    Consistency Check
```

### Code Markers

Every code file must include task references:

```python
# =============================================================================
# FILE: src/config/settings.py
# TASKS: TASK-1.1, TASK-1.2
# PLAN: Section 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
# =============================================================================
```

Every class/function must reference its task:

```python
@dataclass
class UserConfig:  # TASK-1.3 | PLAN-3.2
    """User configuration settings."""
    username: str | None = None
    organizations: list[str] = field(default_factory=list)
```

---

## Task Status Legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed
- `[!]` Blocked

---

## Task Groups Overview

| Group | Tasks | Plan Sections | Status |
|-------|-------|---------------|--------|
| 1. Foundation | TASK-1.1 to TASK-1.6 | 3.1-3.10 (configs) | [x] |
| 2. CLI | TASK-2.1 to TASK-2.3 | 3.1 | [x] |
| 3. Utilities | TASK-3.1 to TASK-3.4 | 3.5, 3.8 | [x] |
| 4. Fetchers | TASK-4.1 to TASK-4.6 | 3.4, 4.3 | [x] |
| 5. Processors | TASK-5.1 to TASK-5.4 | 3.7, 5 | [x] |
| 6. Reporters | TASK-6.1 to TASK-6.4 | 3.6, 5 | [x] |
| 7. Cleanup | TASK-7.1 to TASK-7.2 | 3.9, 3.10 | [x] |
| 8. Integration | TASK-8.1 to TASK-8.2 | 4.1 | [x] |
| 9. Testing | TASK-9.1 to TASK-9.4 | 6 | [x] |

---

## Group 1: Foundation

### TASK-1.1: Project Structure Setup

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.1 |
| **Plan Reference** | Section 4.2 (Module Structure) |
| **Dependencies** | None |
| **Output Files** | Directory structure, `__init__.py` files |
| **Status** | Completed |

#### Description

Create the complete project directory structure with all necessary `__init__.py` files.

#### Directory Structure to Create

```
.scripts/github-activity/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   └── __init__.py
│   ├── fetchers/
│   │   └── __init__.py
│   ├── processors/
│   │   └── __init__.py
│   ├── reporters/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── api_responses/
│   │   └── expected_outputs/
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── e2e/
│       └── __init__.py
├── reports/
├── logs/
│   └── errors/
└── .cache/
```

#### Acceptance Criteria

- [x] All directories created
- [x] All `__init__.py` files created with module docstrings
- [x] `.gitkeep` files in empty directories (reports/, logs/, .cache/)

---

### TASK-1.2: Requirements and Configuration Files

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.2 |
| **Plan Reference** | Section 1 (Technology Stack), Section 6.2 |
| **Dependencies** | TASK-1.1 |
| **Output Files** | `requirements.txt`, `pytest.ini`, `.coveragerc` |
| **Status** | Completed |

#### Description

Create Python dependency file and test configuration.

#### requirements.txt Content

```
# Core
click>=8.0.0
pyyaml>=6.0
jsonschema>=4.0.0

# Utilities
python-dateutil>=2.8.0
rich>=13.0.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0

# Development
black>=23.0.0
ruff>=0.1.0
mypy>=1.0.0
```

#### pytest.ini Content

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*

markers =
    unit: Unit tests (fast, no I/O)
    integration: Integration tests (may use filesystem)
    e2e: End-to-end tests (requires live API)
    slow: Slow tests

addopts =
    -v
    --tb=short
    --strict-markers
    -m "not e2e"
    --cov=src
    --cov-report=term-missing
    --cov-fail-under=80

asyncio_mode = auto
```

#### Acceptance Criteria

- [x] `requirements.txt` includes all dependencies from plan
- [x] `pytest.ini` matches Section 6.2 exactly
- [x] `.coveragerc` configured for src/ coverage

---

### TASK-1.3: Configuration Dataclasses

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.3 |
| **Plan Reference** | Sections 3.2, 3.3, 3.4, 3.5, 3.6, 3.7 |
| **Dependencies** | TASK-1.1 |
| **Output Files** | `src/config/settings.py` |
| **Status** | Completed |

#### Description

Create all configuration dataclasses. Each dataclass default MUST match the plan specification exactly.

#### Dataclasses to Implement

| Dataclass | Plan Section | Fields |
|-----------|--------------|--------|
| `UserConfig` | 3.2 | username, organizations |
| `RepositoryConfig` | 3.3 | include_private, include_forks, exclude |
| `FetchingConfig` | 3.4 | high_activity_threshold, request_delay, max_retries, backoff_base, timeout |
| `CacheConfig` | 3.5 | enabled, directory, ttl_hours |
| `OutputConfig` | 3.6 | directory, formats, include_links, commit_message_format |
| `MetricsConfig` | 3.7 | pr_metrics, review_metrics, engagement_metrics, productivity_patterns, reaction_breakdown |

#### Acceptance Criteria

- [x] All 6 dataclasses implemented
- [x] All defaults match plan specification exactly
- [x] Each class has docstring with plan reference
- [x] Each field has inline comment with plan reference
- [x] File header includes TASKS and PLAN references

---

### TASK-1.4: Logging Configuration Dataclasses

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.4 |
| **Plan Reference** | Sections 3.8, 3.9 |
| **Dependencies** | TASK-1.3 |
| **Output Files** | `src/config/settings.py` (append) |
| **Status** | Completed |

#### Description

Add logging-related configuration dataclasses to settings.py.

#### Acceptance Criteria

- [x] All 5 dataclasses implemented
- [x] All defaults match plan specification exactly
- [x] Nested dataclasses use `field(default_factory=...)`
- [x] Each class has docstring with plan reference

---

### TASK-1.5: Report Cleanup Configuration Dataclasses

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.5 |
| **Plan Reference** | Section 3.10 |
| **Dependencies** | TASK-1.3 |
| **Output Files** | `src/config/settings.py` (append) |
| **Status** | Completed |

#### Description

Add report cleanup configuration dataclasses to settings.py.

#### Acceptance Criteria

- [x] Both dataclasses implemented
- [x] All defaults match plan specification exactly
- [x] Each class has docstring with plan reference

---

### TASK-1.6: Configuration Loader

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-1.6 |
| **Plan Reference** | Section 2.1 (Priority), Section 9 |
| **Dependencies** | TASK-1.3, TASK-1.4, TASK-1.5 |
| **Output Files** | `src/config/loader.py`, `config.yaml` |
| **Status** | Completed |

#### Description

Create configuration loader that merges settings from multiple sources with correct priority.

#### Acceptance Criteria

- [x] ConfigLoader class implemented
- [x] Priority order matches plan Section 2.1
- [x] All ENV variables from plan Section 2.2 mapped
- [x] config.yaml created matching plan Section 9 exactly
- [x] Unit tests for priority order

---

## Group 2: CLI

### TASK-2.1: CLI Entry Point

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-2.1 |
| **Plan Reference** | Section 3.1 |
| **Dependencies** | TASK-1.6 |
| **Output Files** | `generate_report.py` |
| **Status** | Completed |

#### Description

Create the main CLI entry point using Click framework.

#### Acceptance Criteria

- [x] All 12 CLI options implemented
- [x] Short and long option names match plan exactly
- [x] Default values match plan Section 3.1.1
- [x] Help text matches plan descriptions
- [x] `-m` and `-q` are mutually exclusive

---

### TASK-2.2: Smart Defaults Implementation

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-2.2 |
| **Plan Reference** | Section 3.1.1 (Smart Defaults) |
| **Dependencies** | TASK-2.1, TASK-3.1 |
| **Output Files** | `generate_report.py` (update) |
| **Status** | Completed |

#### Description

Implement smart defaults for CLI options.

#### Acceptance Criteria

- [x] `get_current_quarter()` returns correct quarter
- [x] `get_logged_in_user()` uses gh CLI correctly
- [x] Default period is monthly (current month) when no flags
- [x] `-q` without value uses current quarter
- [x] User auto-detection works

---

### TASK-2.3: CLI Validation

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-2.3 |
| **Plan Reference** | Section 3.1.1 |
| **Dependencies** | TASK-2.1 |
| **Output Files** | `generate_report.py` (update) |
| **Status** | Completed |

#### Description

Implement CLI argument validation.

#### Acceptance Criteria

- [x] Mutual exclusivity of -m and -q enforced
- [x] Clear error message when both specified
- [x] All type constraints enforced
- [x] Invalid values rejected with helpful messages

---

## Group 3: Utilities

### TASK-3.1: GitHub CLI Wrapper

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-3.1 |
| **Plan Reference** | Section 4.3 |
| **Dependencies** | TASK-1.1 |
| **Output Files** | `src/utils/gh_client.py` |
| **Status** | Completed |

#### Description

Create a wrapper for the `gh` CLI tool.

#### Acceptance Criteria

- [x] All API commands from plan Section 4.3 supported
- [x] Proper error handling with custom exception
- [x] Timeout configurable
- [x] JSON response parsing
- [x] Pagination support for list endpoints

---

### TASK-3.2: Date Utilities

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-3.2 |
| **Plan Reference** | Section 3.6.3 |
| **Dependencies** | TASK-1.1 |
| **Output Files** | `src/utils/date_utils.py` |
| **Status** | Completed |

#### Description

Create date manipulation utilities for period calculations.

#### Acceptance Criteria

- [x] `get_period_dates()` returns correct ranges for all months
- [x] `get_period_dates()` returns correct ranges for all quarters
- [x] `iter_weeks()` handles partial weeks at boundaries
- [x] `iter_days()` iterates all days inclusive
- [x] Leap year February handled correctly

---

### TASK-3.3: File Utilities

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-3.3 |
| **Plan Reference** | Section 3.6.3 |
| **Dependencies** | TASK-1.1 |
| **Output Files** | `src/utils/file_utils.py` |
| **Status** | Completed |

#### Description

Create file utilities for report naming and path management.

#### Acceptance Criteria

- [x] Monthly pattern matches plan Section 3.6.1
- [x] Quarterly pattern matches plan Section 3.6.1
- [x] Increment logic works (1, 2, 3...)
- [x] Creates year directory if missing
- [x] Returns Path object with correct structure

---

### TASK-3.4: Response Cache

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-3.4 |
| **Plan Reference** | Section 3.5 |
| **Dependencies** | TASK-1.3 |
| **Output Files** | `src/utils/cache.py` |
| **Status** | Completed |

#### Description

Create file-based response cache.

#### Acceptance Criteria

- [x] Cache can be disabled via config
- [x] TTL expiration works correctly
- [x] Cache key hashing produces consistent paths
- [x] JSON serialization/deserialization works
- [x] Cache directory created if missing

---

## Group 4: Fetchers

### TASK-4.1: Base Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.1 |
| **Plan Reference** | Section 3.4 |
| **Dependencies** | TASK-3.1, TASK-3.2, TASK-3.4 |
| **Output Files** | `src/fetchers/base.py` |
| **Status** | Completed |

#### Description

Create abstract base fetcher with adaptive week/day fetching strategy.

#### Acceptance Criteria

- [x] Adaptive fetching uses threshold correctly
- [x] Week iteration handles partial weeks
- [x] Day fallback fetches all days
- [x] Rate limiting respects delay config
- [x] Deduplication removes duplicates
- [x] Abstract methods defined for subclasses

---

### TASK-4.2: Events Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.2 |
| **Plan Reference** | Section 4.3.1 |
| **Dependencies** | TASK-4.1 |
| **Output Files** | `src/fetchers/events.py` |
| **Status** | Completed |

#### Description

Create fetcher for GitHub user events API.

#### Acceptance Criteria

- [x] All event types from plan supported
- [x] Date filtering works correctly
- [x] Caching used for API responses
- [x] Pagination handled
- [x] Event ID extraction for deduplication

---

### TASK-4.3: Commits Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.3 |
| **Plan Reference** | Section 4.3.2 |
| **Dependencies** | TASK-4.1 |
| **Output Files** | `src/fetchers/commits.py` |
| **Status** | Completed |

#### Description

Create fetcher for commits using GitHub Search API.

#### Acceptance Criteria

- [x] Uses gh search commits correctly
- [x] Date range filtering works
- [x] SHA extraction for deduplication
- [x] Caching implemented

---

### TASK-4.4: Pull Requests Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.4 |
| **Plan Reference** | Section 4.3.2 |
| **Dependencies** | TASK-4.1 |
| **Output Files** | `src/fetchers/pull_requests.py` |
| **Status** | Completed |

#### Description

Create fetcher for pull requests using GitHub Search API.

#### Acceptance Criteria

- [x] Uses gh search prs correctly
- [x] Date range filtering works
- [x] PR ID extraction (repo#number) for deduplication
- [x] Caching implemented

---

### TASK-4.5: Issues Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.5 |
| **Plan Reference** | Section 4.3.2 |
| **Dependencies** | TASK-4.1 |
| **Output Files** | `src/fetchers/issues.py` |
| **Status** | Completed |

#### Description

Create fetcher for issues using GitHub Search API.

#### Acceptance Criteria

- [x] Uses gh search issues correctly
- [x] Date range filtering works
- [x] Issue ID extraction for deduplication
- [x] Caching implemented

---

### TASK-4.6: Reviews Fetcher

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-4.6 |
| **Plan Reference** | Section 4.3.4 |
| **Dependencies** | TASK-4.1 |
| **Output Files** | `src/fetchers/reviews.py` |
| **Status** | Completed |

#### Description

Create fetcher for PR reviews.

#### Acceptance Criteria

- [x] Fetches reviews for each PR
- [x] Extracts review state (APPROVED, CHANGES_REQUESTED, etc.)
- [x] Links reviews to PRs correctly
- [x] Caching implemented

---

## Group 5: Processors

### TASK-5.1: Data Aggregator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-5.1 |
| **Plan Reference** | Section 4.1 (Step 3) |
| **Dependencies** | TASK-4.1 to TASK-4.6 |
| **Output Files** | `src/processors/aggregator.py` |
| **Status** | Completed |

#### Description

Create data aggregator to combine and filter fetched data.

#### Acceptance Criteria

- [x] Date filtering works correctly
- [x] All data types aggregated
- [x] Summary statistics calculated
- [x] Deduplication applied

---

### TASK-5.2: PR Metrics Calculator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-5.2 |
| **Plan Reference** | Section 3.7.1, 3.7.3 |
| **Dependencies** | TASK-5.1 |
| **Output Files** | `src/processors/metrics.py` |
| **Status** | Completed |

#### Description

Calculate PR-related metrics.

#### Acceptance Criteria

- [x] All 6 PR metrics calculated correctly
- [x] Handles empty PR list gracefully
- [x] Respects `config.pr_metrics` flag
- [x] Time calculations are accurate

---

### TASK-5.3: Review Metrics Calculator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-5.3 |
| **Plan Reference** | Section 3.7.1, 3.7.3 |
| **Dependencies** | TASK-5.1 |
| **Output Files** | `src/processors/metrics.py` (append) |
| **Status** | Completed |

#### Description

Calculate review-related metrics.

#### Acceptance Criteria

- [x] All 4 review metrics calculated correctly
- [x] Handles empty review list gracefully
- [x] Respects `config.review_metrics` flag

---

### TASK-5.4: Engagement & Productivity Metrics

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-5.4 |
| **Plan Reference** | Section 3.7.1, 3.7.3 |
| **Dependencies** | TASK-5.1 |
| **Output Files** | `src/processors/metrics.py` (append) |
| **Status** | Completed |

#### Description

Calculate engagement metrics and productivity patterns.

#### Acceptance Criteria

- [x] All 3 engagement metrics calculated
- [x] Productivity by day returns all 7 days
- [x] Productivity by hour returns all 24 hours
- [x] Respects config flags

---

## Group 6: Reporters

### TASK-6.1: JSON Report Generator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-6.1 |
| **Plan Reference** | Section 5 (JSON Schema) |
| **Dependencies** | TASK-5.1 to TASK-5.4 |
| **Output Files** | `src/reporters/json_report.py` |
| **Status** | Completed |

#### Description

Generate JSON report matching the schema definition.

#### Acceptance Criteria

- [x] Output matches schema in Section 5 exactly
- [x] All required fields present
- [x] Proper date formatting (ISO 8601)
- [x] Metrics included when calculated

---

### TASK-6.2: Schema Validator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-6.2 |
| **Plan Reference** | Section 5 |
| **Dependencies** | TASK-6.1 |
| **Output Files** | `src/reporters/validator.py`, `src/config/schema.json` |
| **Status** | Completed |

#### Description

Validate JSON report against schema.

#### Acceptance Criteria

- [x] Schema file created matching Section 5
- [x] Validation catches missing required fields
- [x] Validation catches type mismatches
- [x] Returns helpful error messages

---

### TASK-6.3: Markdown Report Generator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-6.3 |
| **Plan Reference** | Section 3.6, 4.1 |
| **Dependencies** | TASK-5.1 to TASK-5.4 |
| **Output Files** | `src/reporters/markdown_report.py` |
| **Status** | Completed |

#### Description

Generate human-readable Markdown report.

#### Acceptance Criteria

- [x] All sections from plan included
- [x] GitHub links included when `include_links=True`
- [x] Commit messages formatted per `commit_message_format`
- [x] Max items per category respected

---

### TASK-6.4: Report Writer

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-6.4 |
| **Plan Reference** | Section 3.6 |
| **Dependencies** | TASK-6.1, TASK-6.3, TASK-3.3 |
| **Output Files** | `src/reporters/writer.py` |
| **Status** | Completed |

#### Description

Write reports to filesystem with proper naming.

#### Acceptance Criteria

- [x] Uses correct file naming from TASK-3.3
- [x] Respects `formats` config
- [x] Creates year directory if needed
- [x] Returns paths of written files

---

## Group 7: Cleanup

### TASK-7.1: Log Cleaner

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-7.1 |
| **Plan Reference** | Section 3.9 |
| **Dependencies** | TASK-1.4 |
| **Output Files** | `src/utils/log_cleanup.py` |
| **Status** | Completed |

#### Description

Implement log cleanup with all thresholds from plan.

#### Acceptance Criteria

- [x] All cleanup operations implemented
- [x] No symlinks used anywhere
- [x] Error log rotation by size works
- [x] Compression of rotated logs works
- [x] All thresholds from plan respected
- [x] Empty directories removed

---

### TASK-7.2: Report Cleaner

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-7.2 |
| **Plan Reference** | Section 3.10 |
| **Dependencies** | TASK-1.5 |
| **Output Files** | `src/utils/report_cleanup.py` |
| **Status** | Completed |

#### Description

Implement report cleanup with all thresholds from plan.

#### Acceptance Criteria

- [x] Version cleanup keeps correct versions
- [x] Age cleanup respects retention
- [x] Archive functionality works
- [x] Compression of archives works
- [x] All thresholds from plan respected

---

## Group 8: Integration

### TASK-8.1: Logger Implementation

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-8.1 |
| **Plan Reference** | Section 3.8 |
| **Dependencies** | TASK-1.4 |
| **Output Files** | `src/utils/logger.py` |
| **Status** | Completed |

#### Description

Implement structured logger with performance tracking.

#### Acceptance Criteria

- [x] All log levels supported
- [x] JSONL format for file logs
- [x] Separate error file
- [x] Timer start/end works
- [x] Slow threshold warnings

---

### TASK-8.2: Main Orchestrator

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-8.2 |
| **Plan Reference** | Section 4.1 |
| **Dependencies** | All previous tasks |
| **Output Files** | `src/orchestrator.py` |
| **Status** | Completed |

#### Description

Create main orchestrator that coordinates all components.

#### Acceptance Criteria

- [x] All steps executed in order
- [x] Errors handled gracefully
- [x] Progress reported to user
- [x] Reports written successfully

---

## Group 9: Testing

### TASK-9.1: Unit Tests - Config

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-9.1 |
| **Plan Reference** | Section 6 |
| **Dependencies** | TASK-1.3 to TASK-1.6 |
| **Output Files** | `tests/unit/test_config_loader.py` |
| **Status** | Completed |

#### Test Cases

- [x] All dataclass defaults match plan
- [x] Config loader priority works
- [x] ENV variables mapped correctly
- [x] YAML parsing works
- [x] Invalid config rejected

---

### TASK-9.2: Unit Tests - Fetchers

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-9.2 |
| **Plan Reference** | Section 6.3 |
| **Dependencies** | TASK-4.1 to TASK-4.6 |
| **Output Files** | `tests/integration/test_fetchers.py` |
| **Status** | Completed |

#### Test Cases

- [x] Adaptive weekly fetching works
- [x] Daily fallback on high activity
- [x] Date filtering works
- [x] Deduplication works
- [x] Caching works

---

### TASK-9.3: Unit Tests - Processors

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-9.3 |
| **Plan Reference** | Section 6.3 |
| **Dependencies** | TASK-5.1 to TASK-5.4 |
| **Output Files** | `tests/unit/test_aggregator.py`, `tests/unit/test_metrics.py` |
| **Status** | Completed |

#### Test Cases

- [x] All PR metrics calculated correctly
- [x] All review metrics calculated correctly
- [x] Engagement metrics calculated correctly
- [x] Productivity patterns calculated correctly
- [x] Empty data handled gracefully

---

### TASK-9.4: Integration Tests

| Attribute | Value |
|-----------|-------|
| **ID** | TASK-9.4 |
| **Plan Reference** | Section 6.3 |
| **Dependencies** | TASK-8.2 |
| **Output Files** | `tests/integration/test_reporters.py`, `tests/integration/test_orchestrator.py`, `tests/integration/test_cleanup.py` |
| **Status** | Completed |

#### Test Cases

- [x] CLI default options work
- [x] Month/quarter mutual exclusivity
- [x] User auto-detection works
- [x] JSON schema validation passes
- [x] Filename increment works
- [x] Empty activity handled

---

## Consistency Verification

### How to Verify Task -> Plan Consistency

1. Check task's "Plan Reference" matches relevant plan section
2. Compare task's "Defaults Reference Table" with plan spec tables
3. Verify implementation template matches plan code samples

### How to Verify Code -> Task Consistency

1. Check file header includes correct TASK-X.Y references
2. Check class/function comments include task and plan references
3. Verify defaults in code match task's "Defaults Reference Table"

### Verification Command

```bash
# Find all task references in code
grep -r "TASK-" src/ --include="*.py"

# Find all plan references in code
grep -r "PLAN-" src/ --include="*.py"

# List tasks not yet implemented
grep -r "TASK-" src/ | cut -d: -f2 | sort -u
```

---

## Task Execution Order

### Phase 1: Foundation
```
TASK-1.1 -> TASK-1.2 -> TASK-1.3 -> TASK-1.4 -> TASK-1.5 -> TASK-1.6
```

### Phase 2: CLI & Utilities
```
TASK-2.1 -> TASK-2.2 -> TASK-2.3
TASK-3.1 -> TASK-3.2 -> TASK-3.3 -> TASK-3.4
```

### Phase 3: Fetchers
```
TASK-4.1 -> TASK-4.2 -> TASK-4.3 -> TASK-4.4 -> TASK-4.5 -> TASK-4.6
```

### Phase 4: Processors
```
TASK-5.1 -> TASK-5.2 -> TASK-5.3 -> TASK-5.4
```

### Phase 5: Reporters
```
TASK-6.1 -> TASK-6.2 -> TASK-6.3 -> TASK-6.4
```

### Phase 6: Cleanup & Integration
```
TASK-7.1 -> TASK-7.2
TASK-8.1 -> TASK-8.2
```

### Phase 7: Testing
```
TASK-9.1 -> TASK-9.2 -> TASK-9.3 -> TASK-9.4
```

---

*Document Version: 1.3*
*Last Updated: 2026-01-03*
*Phase 6 Completed: 2026-01-03*
*All Phases Complete*
*Linked Plan: plan-v2.md*
