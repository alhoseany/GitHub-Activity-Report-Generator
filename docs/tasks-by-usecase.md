# GitHub Activity Report Generator - Tasks by Use Case

> **User-Centric Task Organization**
>
> Tasks grouped by what users want to accomplish, not by code modules.

---

## Traceability

This document reorganizes tasks from `tasks.md` by use case. Each task references:
- **Original Task ID** from tasks.md (TASK-X.Y)
- **Plan Section** from plan-v2.md

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐
│  Use Case Tasks │────▶│  tasks.md   │────▶│  plan-v2.md │
│  (this file)    │     │  TASK-X.Y   │     │  Section X  │
└─────────────────┘     └─────────────┘     └─────────────┘
```

---

## Use Case Overview

| Use Case | Description | Tasks Involved |
|----------|-------------|----------------|
| UC-1 | First-Time Setup | TASK-1.1, TASK-1.2 |
| UC-2 | Generate Basic Report | TASK-2.1, TASK-2.2, TASK-4.1-4.6, TASK-5.1, TASK-6.1, TASK-6.3, TASK-6.4, TASK-8.2 |
| UC-3 | Generate Report for Specific Period | TASK-2.1, TASK-2.3, TASK-3.2 |
| UC-4 | Filter by User/Organization | TASK-1.3, TASK-1.6, TASK-2.1 |
| UC-5 | Filter Repositories | TASK-1.3, TASK-1.6, TASK-2.1 |
| UC-6 | Customize Output Format | TASK-1.3, TASK-1.6, TASK-6.1, TASK-6.3, TASK-6.4 |
| UC-7 | Enable/Disable Metrics | TASK-1.3, TASK-5.2, TASK-5.3, TASK-5.4 |
| UC-8 | Control Caching Behavior | TASK-1.3, TASK-3.4, TASK-2.1 |
| UC-9 | Configure Logging | TASK-1.4, TASK-8.1 |
| UC-10 | Manage Disk Space (Logs) | TASK-1.4, TASK-7.1 |
| UC-11 | Manage Disk Space (Reports) | TASK-1.5, TASK-7.2 |
| UC-12 | Validate Report Output | TASK-6.2 |
| UC-13 | Run Tests | TASK-9.1, TASK-9.2, TASK-9.3, TASK-9.4 |

---

## UC-1: First-Time Setup

**Goal:** Set up the project for first use.

**User Story:** As a new user, I want to install and configure the tool so I can start generating reports.

### Tasks

#### UC-1.1: Create Project Structure

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-1.1 |
| **Plan Reference** | Section 4.2 |
| **Dependencies** | None |

**What to Create:**

```
.scripts/github-activity/
├── src/
│   ├── config/
│   ├── fetchers/
│   ├── processors/
│   ├── reporters/
│   └── utils/
├── tests/
│   ├── fixtures/
│   │   ├── api_responses/
│   │   └── expected_outputs/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── reports/
├── logs/
│   └── errors/
└── .cache/
```

**Acceptance Criteria:**
- [ ] All directories created
- [ ] All `__init__.py` files present
- [ ] `.gitkeep` in empty directories

---

#### UC-1.2: Install Dependencies

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-1.2 |
| **Plan Reference** | Section 1, 6.2 |
| **Dependencies** | UC-1.1 |

**Files to Create:**

1. `requirements.txt` with:
   - click>=8.0.0
   - pyyaml>=6.0
   - jsonschema>=4.0.0
   - python-dateutil>=2.8.0
   - rich>=13.0.0
   - pytest>=7.0.0 (+ pytest-cov, pytest-asyncio, pytest-mock)
   - black>=23.0.0, ruff>=0.1.0, mypy>=1.0.0

2. `pytest.ini` with test configuration

**Acceptance Criteria:**
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pytest` runs without import errors

---

## UC-2: Generate Basic Report

**Goal:** Generate a monthly report for the current month with default settings.

**User Story:** As a user, I want to run the tool with minimal input and get a useful activity report.

### Tasks

#### UC-2.1: Create CLI Entry Point

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-2.1, TASK-2.2 |
| **Plan Reference** | Section 3.1 |
| **Dependencies** | UC-1 complete |

**CLI Command:**

```bash
./generate_report.py
# OR
./generate_report.py -m  # Explicit monthly
```

**Smart Defaults:**
- No flags → Monthly report for current month
- User → Auto-detect from `gh api /user`
- Year → Current year
- Format → Both JSON and Markdown

**Implementation Requirements:**
- Click framework
- All 12 CLI options from plan Section 3.1.1
- User auto-detection via gh CLI

**Acceptance Criteria:**
- [ ] Running with no args generates current month report
- [ ] User auto-detected from gh CLI
- [ ] Both JSON and Markdown files created

---

#### UC-2.2: Fetch GitHub Data

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-3.1, TASK-4.1 to TASK-4.6 |
| **Plan Reference** | Sections 3.4, 4.3 |
| **Dependencies** | UC-2.1 |

**Data to Fetch:**

| Data Type | API | Fetcher |
|-----------|-----|---------|
| Events | `/users/{user}/events` | EventsFetcher |
| Commits | `gh search commits` | CommitsFetcher |
| Pull Requests | `gh search prs` | PullRequestsFetcher |
| Issues | `gh search issues` | IssuesFetcher |
| Reviews | `/repos/{owner}/{repo}/pulls/{n}/reviews` | ReviewsFetcher |

**Adaptive Fetching Strategy:**
1. Fetch by week (7-day chunks)
2. If week has ≥100 events → refetch day-by-day
3. Deduplicate results

**Acceptance Criteria:**
- [ ] All 5 data types fetched
- [ ] Adaptive strategy switches to daily when needed
- [ ] Rate limiting (1 second between requests)
- [ ] Caching of responses

---

#### UC-2.3: Process and Aggregate Data

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-5.1 |
| **Plan Reference** | Section 4.1 (Step 3) |
| **Dependencies** | UC-2.2 |

**Processing Steps:**
1. Filter by date range
2. Deduplicate records
3. Group by type
4. Calculate summary statistics

**Output:**
```python
AggregatedData(
    commits=[...],
    pull_requests=[...],
    issues=[...],
    reviews=[...],
    comments=[...]
)
```

**Acceptance Criteria:**
- [ ] Date filtering works correctly
- [ ] Summary statistics calculated
- [ ] No duplicate records

---

#### UC-2.4: Generate Reports

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-6.1, TASK-6.3, TASK-6.4 |
| **Plan Reference** | Section 3.6, 5 |
| **Dependencies** | UC-2.3 |

**Output Files:**

| Format | Pattern | Example |
|--------|---------|---------|
| Markdown | `{year}-{MM}-github-activity-{n}.md` | `2024-12-github-activity-1.md` |
| JSON | `{year}-{MM}-github-activity-{n}.json` | `2024-12-github-activity-1.json` |

**Directory Structure:**
```
reports/
└── 2024/
    └── octocat/
        ├── 2024-12-github-activity-1.md
        └── 2024-12-github-activity-1.json
```

Note: Reports are grouped by year and username for better organization.

**Acceptance Criteria:**
- [x] Files created in correct location
- [x] Filename increments if already exists
- [x] JSON matches schema from Section 5
- [x] Markdown is human-readable

---

#### UC-2.5: Orchestrate Full Pipeline

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-8.2 |
| **Plan Reference** | Section 4.1 |
| **Dependencies** | UC-2.1 through UC-2.4 |

**Pipeline Flow:**
```
1. Load config
2. Initialize logger
3. Run cleanup (if trigger=startup)
4. Fetch data
5. Aggregate data
6. Calculate metrics
7. Generate reports
8. Run cleanup (if trigger=shutdown)
```

**Acceptance Criteria:**
- [ ] All steps execute in order
- [ ] Errors handled gracefully
- [ ] Progress shown to user
- [ ] Reports written successfully

---

## UC-3: Generate Report for Specific Period

**Goal:** Generate a report for a specific month, quarter, or year.

**User Story:** As a user, I want to generate a report for a past period to review my historical activity.

### Tasks

#### UC-3.1: Support Period Selection

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-2.1, TASK-2.3, TASK-3.2 |
| **Plan Reference** | Section 3.1.1 |
| **Dependencies** | UC-2.1 |

**CLI Options:**

| Option | Example | Result |
|--------|---------|--------|
| `-m 6` | `./generate_report.py -m 6` | June of current year |
| `-m 6 -y 2023` | `./generate_report.py -m 6 -y 2023` | June 2023 |
| `-q 2` | `./generate_report.py -q 2` | Q2 of current year |
| `-q 4 -y 2023` | `./generate_report.py -q 4 -y 2023` | Q4 2023 |

**Validation Rules:**
- `-m` and `-q` are mutually exclusive
- Month: 1-12
- Quarter: 1-4
- Year: reasonable range (2000-2100)

**Quarter Date Ranges:**

| Quarter | Start | End |
|---------|-------|-----|
| Q1 | Jan 1 | Mar 31 |
| Q2 | Apr 1 | Jun 30 |
| Q3 | Jul 1 | Sep 30 |
| Q4 | Oct 1 | Dec 31 |

**Acceptance Criteria:**
- [ ] Monthly selection works
- [ ] Quarterly selection works
- [ ] Year override works
- [ ] Cannot use -m and -q together
- [ ] Clear error messages for invalid input

---

## UC-4: Filter by User/Organization

**Goal:** Generate a report for a specific user or filter by organizations.

**User Story:** As a team lead, I want to generate reports for team members or filter to specific organizations.

### Tasks

#### UC-4.1: Configure User Settings

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.3, TASK-1.6, TASK-2.1 |
| **Plan Reference** | Section 3.2 |
| **Dependencies** | UC-1 |

**Configuration Options:**

| Setting | CLI | Config | ENV | Default |
|---------|-----|--------|-----|---------|
| Username | `-u/--user` | `user.username` | `GITHUB_ACTIVITY_USER` | gh logged-in user |
| Organizations | - | `user.organizations` | - | all |

**Examples:**

```bash
# Specific user
./generate_report.py -u octocat
```

**config.yaml:**
```yaml
user:
  username: null    # null = auto-detect
  organizations: [] # [] = all orgs (config-only, no CLI option)
```

**Acceptance Criteria:**
- [x] User auto-detection works
- [x] Explicit user override works
- [x] Organization filtering works (via config)
- [x] Multiple orgs supported (in config array)

---

## UC-5: Filter Repositories

**Goal:** Include or exclude specific repositories from the report.

**User Story:** As a user, I want to exclude personal forks and certain repositories from my work report.

### Tasks

#### UC-5.1: Configure Repository Filters

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.3, TASK-1.6, TASK-2.1 |
| **Plan Reference** | Section 3.3 |
| **Dependencies** | UC-1 |

**Configuration Options:**

| Setting | CLI | Config | Default |
|---------|-----|--------|---------|
| Include Private | - | `repositories.include_private` | true |
| Include Forks | - | `repositories.include_forks` | false |
| Include List | `--include-repos` | `repositories.include` | [] |
| Exclude List | `--exclude-repos` | `repositories.exclude` | [] |

**Examples:**

```bash
# Include only specific repos (whitelist)
./generate_report.py --include-repos "owner/repo1,owner/repo2"

# Exclude specific repos (blacklist)
./generate_report.py --exclude-repos "owner/fork1,owner/fork2"

# Use wildcards in config for patterns like "owner/*"
```

**config.yaml:**
```yaml
repositories:
  include_private: true
  include_forks: false
  include: []              # whitelist (empty = all repos)
  exclude:                 # blacklist
    - "owner/repo-to-skip"
    - "owner/*-fork"       # supports wildcards
```

**Acceptance Criteria:**
- [x] Private repos included by default (config-only)
- [x] Forks excluded by default (config-only)
- [x] Include list (whitelist) filters repos via CLI or config
- [x] Exclude list (blacklist) filters repos via CLI or config
- [x] Wildcard patterns supported (e.g., `owner/*`)

---

## UC-6: Customize Output Format

**Goal:** Control the format, location, and content of generated reports.

**User Story:** As a user, I want to generate only JSON reports in a custom directory.

### Tasks

#### UC-6.1: Configure Output Settings

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.3, TASK-1.6, TASK-6.1, TASK-6.3, TASK-6.4, TASK-3.3 |
| **Plan Reference** | Section 3.6 |
| **Dependencies** | UC-1 |

**Configuration Options:**

| Setting | CLI | Config | ENV | Default |
|---------|-----|--------|-----|---------|
| Directory | `-o/--output-dir` | `output.directory` | `GITHUB_ACTIVITY_OUTPUT_DIR` | "reports" |
| Formats | `-f/--format` | `output.formats` | - | ["json", "markdown"] |
| Include Links | - | `output.include_links` | - | true |
| Commit Format | - | `output.commit_message_format` | - | "truncated" |

**Format Options:**
- `json` - Only JSON
- `markdown` - Only Markdown
- `both` - Both formats (default)

**Commit Message Format Options:**
- `truncated` - First 100 characters (default)
- `first_line` - First line only
- `full` - Complete message

**Examples:**

```bash
# Only JSON to custom dir
./generate_report.py -f json --output-dir ~/my-reports

# Only markdown
./generate_report.py -f markdown
```

**config.yaml:**
```yaml
output:
  directory: "reports"
  formats: ["json", "markdown"]
  include_links: true
  commit_message_format: "truncated"
```

**Acceptance Criteria:**
- [x] Output directory customizable
- [x] Format selection works
- [x] Links included/excluded correctly
- [x] Commit messages formatted correctly

---

## UC-7: Enable/Disable Metrics

**Goal:** Control which metrics are calculated and included in reports.

**User Story:** As a user, I want to disable productivity patterns to speed up report generation.

### Tasks

#### UC-7.1: Configure Metrics

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.3, TASK-5.2, TASK-5.3, TASK-5.4 |
| **Plan Reference** | Section 3.7 |
| **Dependencies** | UC-1 |

**Metrics Categories:**

| Category | Config Key | Default | What It Calculates |
|----------|------------|---------|-------------------|
| PR Metrics | `metrics.pr_metrics` | true | avg commits/PR, merge time, review iterations |
| Review Metrics | `metrics.review_metrics` | true | turnaround time, approvals, changes requested |
| Engagement | `metrics.engagement_metrics` | true | response time, collaboration score |
| Productivity | `metrics.productivity_patterns` | true | by day of week, by hour |
| Reactions | `metrics.reaction_breakdown` | true | reaction counts by type |

**config.yaml:**
```yaml
metrics:
  pr_metrics: true
  review_metrics: true
  engagement_metrics: true
  productivity_patterns: true
  reaction_breakdown: true
```

**Acceptance Criteria:**
- [ ] Each metric category can be disabled
- [ ] Disabled metrics not calculated (saves time)
- [ ] Disabled metrics not in output
- [ ] All enabled by default

---

## UC-8: Control Caching Behavior

**Goal:** Speed up repeated runs with caching or force fresh data.

**User Story:** As a user, I want to disable cache to get the latest data after making changes.

### Tasks

#### UC-8.1: Configure Caching

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.3, TASK-3.4, TASK-2.1 |
| **Plan Reference** | Section 3.5 |
| **Dependencies** | UC-1 |

**Configuration Options:**

| Setting | CLI | Config | ENV | Default |
|---------|-----|--------|-----|---------|
| Enabled | `--no-cache` | `cache.enabled` | - | true |
| Directory | - | `cache.directory` | `GITHUB_ACTIVITY_CACHE_DIR` | ".cache" |
| TTL Hours | - | `cache.ttl_hours` | - | 24 |

**Examples:**

```bash
# Force fresh data
./generate_report.py --no-cache

# Use cache (default)
./generate_report.py
```

**config.yaml:**
```yaml
cache:
  enabled: true
  directory: ".cache"
  ttl_hours: 24
```

**How Caching Works:**
1. API responses cached as JSON files
2. Cache key = hash of request parameters
3. Expired files deleted on access
4. `--no-cache` bypasses all cache reads

**Acceptance Criteria:**
- [ ] Cache speeds up repeated runs
- [ ] `--no-cache` forces fresh API calls
- [ ] TTL expiration works
- [ ] Cache directory configurable

---

## UC-9: Configure Logging

**Goal:** Control log output for debugging and monitoring.

**User Story:** As a user, I want verbose output to troubleshoot issues.

### Tasks

#### UC-9.1: Configure Logging Settings

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.4, TASK-8.1 |
| **Plan Reference** | Section 3.8 |
| **Dependencies** | UC-1 |

**Configuration Options:**

| Setting | CLI | Config | ENV | Default |
|---------|-----|--------|-----|---------|
| Level | `--log-level` | `logging.level` | `GITHUB_ACTIVITY_LOG_LEVEL` | "INFO" |
| Log Dir | - | `logging.file.directory` | `GITHUB_ACTIVITY_LOG_DIR` | "logs" |
| Colorize | - | `logging.colorize` | - | true |
| Progress | - | `logging.progress_style` | - | "rich" |

**Log Level Options:**
- `DEBUG` - Detailed debugging information
- `INFO` - General information (default)
- `WARNING` - Warning messages only
- `ERROR` - Error messages only

**config.yaml:**
```yaml
logging:
  level: "INFO"
  colorize: true
  show_timestamps: true
  progress_style: "rich"
  file:
    enabled: true
    directory: "logs"
    organize_by_date: true
    format: "jsonl"
    separate_errors: true
    error_file: "errors.log"
```

**Acceptance Criteria:**
- [x] Log level selection works
- [x] File logging enabled
- [x] Errors go to separate file
- [x] Progress bar shows

---

## UC-10: Manage Disk Space (Logs)

**Goal:** Automatically clean up old log files to prevent disk space issues.

**User Story:** As a user, I want logs automatically cleaned up so they don't fill my disk.

### Tasks

#### UC-10.1: Configure Log Cleanup

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.4, TASK-7.1 |
| **Plan Reference** | Section 3.9 |
| **Dependencies** | UC-9 |

**Cleanup Thresholds:**

| Setting | Default | Description |
|---------|---------|-------------|
| `trigger` | "startup" | When to run cleanup |
| `retention_days` | 30 | Delete activity logs after |
| `retention_days_performance` | 14 | Delete perf logs after |
| `max_total_size_mb` | 500 | Max total log size |
| `max_file_size_mb` | 50 | Max single file size |
| `max_files` | 100 | Max number of log files |
| `keep_minimum_days` | 7 | Always keep recent logs |
| `strategy` | "oldest_first" | Delete oldest first |

**Error Log Rotation:**

| Setting | Default | Description |
|---------|---------|-------------|
| `error_log.max_size_mb` | 10 | Rotate when exceeds |
| `error_log.max_files` | 50 | Max rotated files |
| `error_log.max_age_days` | 365 | Delete old error logs |
| `error_log.compress_rotated` | true | Gzip rotated logs |

**Rotation Process (No Symlinks):**
```
When errors.log > 10MB:
1. Move: errors.log → errors/errors_{timestamp}.log
2. Compress: → errors/errors_{timestamp}.log.gz
3. Create new empty: errors.log
```

**config.yaml:**
```yaml
logging:
  file:
    cleanup:
      trigger: "startup"
      retention_days: 30
      retention_days_performance: 14
      max_total_size_mb: 500
      max_file_size_mb: 50
      max_files: 100
      keep_minimum_days: 7
      strategy: "oldest_first"
      error_log:
        max_size_mb: 10
        max_files: 50
        max_age_days: 365
        compress_rotated: true
```

**Acceptance Criteria:**
- [ ] Old logs deleted automatically
- [ ] Size limits enforced
- [ ] Error log rotation works
- [ ] Compression works
- [ ] No symlinks used

---

## UC-11: Manage Disk Space (Reports)

**Goal:** Automatically clean up old reports and archive historical data.

**User Story:** As a user, I want old reports archived and excess versions cleaned up.

### Tasks

#### UC-11.1: Configure Report Cleanup

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-1.5, TASK-7.2 |
| **Plan Reference** | Section 3.10 |
| **Dependencies** | UC-6 |

**Cleanup Thresholds:**

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | true | Enable cleanup |
| `trigger` | "startup" | When to run |
| `retention_years` | 2 | Keep reports for |
| `keep_versions` | 3 | Versions per period |
| `max_total_size_mb` | 1000 | Max total size |
| `max_file_size_mb` | 100 | Max single file |
| `max_reports` | 500 | Max report count |
| `keep_minimum_months` | 6 | Always keep recent |
| `strategy` | "oldest_first" | Delete oldest first |

**Version Cleanup Example:**
```
Period: 2024-12
Files: 2024-12-github-activity-1.md, -2.md, -3.md, -4.md, -5.md
keep_versions: 3
Result: Keep -3, -4, -5; Delete -1, -2
```

**Archive Settings:**

| Setting | Default | Description |
|---------|---------|-------------|
| `archive.enabled` | true | Enable archiving |
| `archive.directory` | "reports/archive" | Archive location |
| `archive.compress` | true | Compress archives |
| `archive.archive_after_days` | 365 | Archive after |

**config.yaml:**
```yaml
output_cleanup:
  enabled: true
  trigger: "startup"
  retention_years: 2
  keep_versions: 3
  max_total_size_mb: 1000
  max_file_size_mb: 100
  max_reports: 500
  keep_minimum_months: 6
  strategy: "oldest_first"
  archive:
    enabled: true
    directory: "reports/archive"
    compress: true
    archive_after_days: 365
```

**Acceptance Criteria:**
- [ ] Old versions cleaned up
- [ ] Only keep_versions kept per period
- [ ] Archive works with compression
- [ ] Size limits enforced

---

## UC-12: Validate Report Output

**Goal:** Ensure generated reports meet the schema specification.

**User Story:** As a developer, I want to validate that reports match the expected schema.

### Tasks

#### UC-12.1: Implement Schema Validation

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-6.2 |
| **Plan Reference** | Section 5 |
| **Dependencies** | UC-2.4 |

**Schema Location:** `src/config/schema.json`

**Validation Points:**
- Required fields present
- Correct data types
- Enum values valid
- Nested structure correct

**Usage:**
```python
from src.reporters.validator import validate_report

is_valid, errors = validate_report(report_data)
if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
```

**Acceptance Criteria:**
- [ ] Schema file matches Section 5
- [ ] Missing fields detected
- [ ] Type errors detected
- [ ] Helpful error messages

---

## UC-13: Run Tests

**Goal:** Verify the tool works correctly.

**User Story:** As a developer, I want to run tests to ensure code quality.

### Tasks

#### UC-13.1: Run Unit Tests

| Attribute | Value |
|-----------|-------|
| **Original Tasks** | TASK-9.1, TASK-9.2, TASK-9.3 |
| **Plan Reference** | Section 6 |
| **Dependencies** | Implementation complete |

**Test Commands:**
```bash
# All unit tests
pytest tests/unit/ -v

# Specific module
pytest tests/unit/test_config.py -v
pytest tests/unit/test_fetchers.py -v
pytest tests/unit/test_processors.py -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=html
```

**Test Categories:**
- Config tests: dataclass defaults, loader priority
- Fetcher tests: adaptive strategy, deduplication
- Processor tests: metrics calculations

**Acceptance Criteria:**
- [ ] 80% code coverage minimum
- [ ] All tests pass
- [ ] No import errors

---

#### UC-13.2: Run Integration Tests

| Attribute | Value |
|-----------|-------|
| **Original Task** | TASK-9.4 |
| **Plan Reference** | Section 6.3 |
| **Dependencies** | UC-13.1 |

**Test Commands:**
```bash
# Integration tests
pytest tests/integration/ -v

# E2E tests (requires gh CLI)
pytest tests/e2e/ -v -m e2e
```

**Integration Test Coverage:**
- CLI argument parsing
- Config file loading
- Report generation pipeline
- File output

**Acceptance Criteria:**
- [ ] CLI works end-to-end
- [ ] Config loading works
- [ ] Report files generated correctly

---

## Implementation Order by Use Case

### Phase 1: Core Setup
```
UC-1.1 → UC-1.2 (Project structure and dependencies)
```

### Phase 2: Basic Functionality
```
UC-2.1 → UC-2.2 → UC-2.3 → UC-2.4 → UC-2.5 (Generate basic report)
```

### Phase 3: Period & Filtering
```
UC-3.1 (Period selection)
UC-4.1 (User filtering)
UC-5.1 (Repo filtering)
```

### Phase 4: Customization
```
UC-6.1 (Output format)
UC-7.1 (Metrics)
UC-8.1 (Caching)
```

### Phase 5: Operations
```
UC-9.1 (Logging)
UC-10.1 (Log cleanup)
UC-11.1 (Report cleanup)
```

### Phase 6: Quality
```
UC-12.1 (Validation)
UC-13.1 → UC-13.2 (Testing)
```

---

## Cross-Reference: Use Case Tasks → Original Tasks

| UC Task | Original Task(s) | Primary Plan Section |
|---------|------------------|---------------------|
| UC-1.1 | TASK-1.1 | 4.2 |
| UC-1.2 | TASK-1.2 | 1, 6.2 |
| UC-2.1 | TASK-2.1, TASK-2.2 | 3.1 |
| UC-2.2 | TASK-3.1, TASK-4.1-4.6 | 3.4, 4.3 |
| UC-2.3 | TASK-5.1 | 4.1 |
| UC-2.4 | TASK-6.1, TASK-6.3, TASK-6.4 | 3.6, 5 |
| UC-2.5 | TASK-8.2 | 4.1 |
| UC-3.1 | TASK-2.1, TASK-2.3, TASK-3.2 | 3.1.1 |
| UC-4.1 | TASK-1.3, TASK-1.6, TASK-2.1 | 3.2 |
| UC-5.1 | TASK-1.3, TASK-1.6, TASK-2.1 | 3.3 |
| UC-6.1 | TASK-1.3, TASK-1.6, TASK-6.1, TASK-6.3, TASK-6.4, TASK-3.3 | 3.6 |
| UC-7.1 | TASK-1.3, TASK-5.2, TASK-5.3, TASK-5.4 | 3.7 |
| UC-8.1 | TASK-1.3, TASK-3.4, TASK-2.1 | 3.5 |
| UC-9.1 | TASK-1.4, TASK-8.1 | 3.8 |
| UC-10.1 | TASK-1.4, TASK-7.1 | 3.9 |
| UC-11.1 | TASK-1.5, TASK-7.2 | 3.10 |
| UC-12.1 | TASK-6.2 | 5 |
| UC-13.1 | TASK-9.1, TASK-9.2, TASK-9.3 | 6 |
| UC-13.2 | TASK-9.4 | 6.3 |

---

*Document Version: 1.1*
*Last Updated: 2026-01-04*
*Linked Documents: tasks.md, plan-v2.md*

**Changelog:**
- v1.1 (2026-01-04): Updated specs to match implementation
  - UC-4.1: Removed `-o/--orgs` CLI option (organizations is config-only)
  - UC-5.1: Replaced `--include-private`/`--include-forks` with `--include-repos`/`--exclude-repos`
  - UC-6.1: Changed `commit_message_format` default to `"truncated"`
  - UC-9.1: Replaced `-v/--verbose` with explicit `--log-level`
  - UC-2.4: Updated directory structure to show user grouping
