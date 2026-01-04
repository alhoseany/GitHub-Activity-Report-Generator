# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Activity Report Generator - A Python CLI tool that uses the local `gh` CLI to fetch GitHub activity data and generate monthly/quarterly reports in JSON and Markdown formats.

## Commands

### Running the CLI
```bash
# Generate report for current month
python generate_report.py

# Monthly report for specific month/year
python generate_report.py -m 6 -y 2024

# Quarterly report
python generate_report.py -q 2 -y 2024

# For specific user (auto-detects from gh CLI if omitted)
python generate_report.py -u username

# Filter repositories
python generate_report.py --include-repos "owner/repo1,owner/repo2"
python generate_report.py --exclude-repos "owner/fork1"

# Dry run (shows what would be fetched)
python generate_report.py --dry-run

# Skip cache
python generate_report.py --no-cache
```

### Testing
```bash
# Run all tests (excludes e2e by default)
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_metrics.py

# Run specific test
pytest tests/unit/test_metrics.py::test_function_name -v

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m unit
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Pipeline Flow
```
CLI (generate_report.py)
    └── ReportOrchestrator (src/orchestrator.py)
            ├── ConfigLoader - loads config.yaml + env vars
            ├── Fetchers - fetch data from GitHub via gh CLI
            ├── DataAggregator - combine and deduplicate data
            ├── MetricsCalculator - compute statistics
            ├── Reporters - generate JSON/Markdown output
            └── Cleaners - log and report cleanup
```

### Key Modules

**Entry Point:**
- `generate_report.py` - Click-based CLI, handles argument parsing and validation

**Orchestration:**
- `src/orchestrator.py` - `ReportOrchestrator` coordinates the entire pipeline

**Configuration:**
- `src/config/settings.py` - Dataclasses for all config sections (period, user, repos, cache, output, metrics, logging, cleanup)
- `src/config/loader.py` - Loads config with priority: CLI > ENV > config.yaml > defaults
- `config.yaml` - User configuration file

**Fetchers (`src/fetchers/`):**
- `base.py` - `BaseFetcher` with adaptive week/day fetching strategy
- `commits.py`, `pull_requests.py`, `issues.py`, `reviews.py`, `events.py`, `comments.py` - Specific data fetchers

**Processors (`src/processors/`):**
- `aggregator.py` - `DataAggregator` combines fetched data, handles deduplication
- `metrics.py` - `MetricsCalculator` computes PR metrics, review metrics, productivity patterns

**Reporters (`src/reporters/`):**
- `json_report.py` - Generates JSON reports validated against schema
- `markdown_report.py` - Generates human-readable Markdown reports
- `validator.py` - JSON schema validation

**Utilities (`src/utils/`):**
- `gh_client.py` - `GitHubClient` wrapper around `gh` CLI
- `cache.py` - File-based response caching with TTL
- `date_utils.py` - Period calculations (month/quarter ranges)
- `file_utils.py` - Report file naming with auto-increment
- `repo_filter.py` - Whitelist/blacklist filtering with glob patterns
- `logger.py` - Structured logging with Rich
- `log_cleanup.py`, `report_cleanup.py` - Cleanup utilities

**Documentation (`docs/`):**
- `MEMORY.md` - **Read first when starting a session.** Project context, current status, implementation checklist (UC-1.1 through UC-13.2), key decisions, important defaults, progress log. Update when making progress or ending a session.
- `PROJECT.md` - Original project requirements and goals
- `implement.md` - Step-by-step implementation guide with code examples
- `tasks-by-usecase.md` - Tasks organized by use case with acceptance criteria
- `tasks.md` - Technical task breakdown with TASK-X.Y identifiers that map to code comments
- `plan-v2.md` - Full specifications: CLI interface, user settings, repo filters, fetching strategy, caching, output, metrics, logging, cleanup. Master reference for all config options.
- `plan.md` - Original planning document

### Configuration Priority
1. CLI arguments (highest)
2. Environment variables (`GITHUB_ACTIVITY_USER`, `GITHUB_ACTIVITY_OUTPUT_DIR`, etc.)
3. config.yaml
4. Dataclass defaults (lowest)

### Data Flow
1. Fetchers use adaptive strategy: fetch by week, fall back to day-by-day if high activity
2. All fetchers use `gh` CLI subprocess calls via `GitHubClient`
3. Results are cached to `.cache/` with configurable TTL
4. Data is aggregated, deduplicated by ID/SHA
5. Reports saved to `reports/YEAR/YEAR-MM-github-activity-N.{json,md}`

## Code Conventions

- Each file has a header comment with TASKS and PLAN references linking to `docs/tasks.md`
- Functions/classes include UC (use case) and PLAN references in comments
- All configuration uses dataclasses in `src/config/settings.py`
- Fetchers inherit from `BaseFetcher` and override `_fetch_range()` and `_get_event_id()`
