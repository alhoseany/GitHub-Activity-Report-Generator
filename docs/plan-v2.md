# GitHub Activity Report Generator - Implementation Plan v2

> **Single Source of Truth** for the GitHub Activity Report Generator
>
> **Document Structure:** Each feature uses Specification-Implementation pattern for easy consistency verification.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Master Reference](#2-master-reference)
3. [Feature Specifications](#3-feature-specifications)
   - [3.1 CLI Interface](#31-cli-interface)
   - [3.2 User Settings](#32-user-settings)
   - [3.3 Repository Filters](#33-repository-filters)
   - [3.4 Fetching Strategy](#34-fetching-strategy)
   - [3.5 Caching](#35-caching)
   - [3.6 Output & Reports](#36-output--reports)
   - [3.7 Metrics](#37-metrics)
   - [3.8 Logging](#38-logging)
   - [3.9 Log Cleanup](#39-log-cleanup)
   - [3.10 Report Cleanup](#310-report-cleanup)
4. [Architecture](#4-architecture)
   - [4.1 Data Flow](#41-data-flow)
   - [4.2 Module Structure](#42-module-structure)
   - [4.3 GitHub API Data Sources](#43-github-api-data-sources)
5. [JSON Schema](#5-json-schema)
6. [Testing Strategy](#6-testing-strategy)
7. [Error Handling](#7-error-handling)
8. [Implementation Phases](#8-implementation-phases)
9. [Configuration File](#9-configuration-file)

---

## 1. Executive Summary

### Purpose
Python-based GitHub Activity Report Generator using the local `gh` CLI to fetch user activity data and generate comprehensive monthly or quarterly reports.

### Key Features
- Flexible period support: Monthly or Quarterly activity aggregation
- Activity tracking: commits, PRs, issues, reviews, comments
- Advanced metrics (PR approval times, commits per PR, response times)
- JSON output validated against a defined schema
- Markdown reports with metadata and quick stats
- Adaptive fetching to avoid API rate limits
- Extensive logging with cleanup thresholds
- No symlinks used anywhere

### Technology Stack
| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| CLI Tool | GitHub CLI (`gh`) |
| Output Format | JSON (validated) + Markdown |
| Schema Validation | jsonschema library |
| Testing | pytest |
| CLI Framework | click |

---

## 2. Master Reference

### 2.1 Configuration Priority

```
CLI Arguments > Environment Variables > config.yaml > Built-in Defaults
```

### 2.2 All Settings Cross-Reference

| Setting | Config Key | CLI Short | CLI Long | ENV Variable | Default |
|---------|------------|-----------|----------|--------------|---------|
| Default Period Type | `period.default_type` | - | - | - | monthly |
| Year | *(CLI only)* | `-y` | `--year` | - | current year |
| Month | *(CLI only)* | `-m` | `--month` | - | current month |
| Quarter | *(CLI only)* | `-q` | `--quarter` | - | current quarter |
| GitHub User | `user.username` | `-u` | `--user` | `GITHUB_ACTIVITY_USER` | logged-in user |
| Organizations | `user.organizations` | - | - | - | all accessible |
| Include Private | `repositories.include_private` | - | - | - | true |
| Include Forks | `repositories.include_forks` | - | - | - | false |
| Include Repos | `repositories.include` | - | `--include-repos` | - | [] |
| Exclude Repos | `repositories.exclude` | - | `--exclude-repos` | - | [] |
| High Activity Threshold | `fetching.high_activity_threshold` | - | - | `GITHUB_ACTIVITY_HIGH_THRESHOLD` | 100 |
| Request Delay | `fetching.request_delay` | - | - | - | 1.0 |
| Cache Enabled | `cache.enabled` | - | `--no-cache` | - | true |
| Cache TTL | `cache.ttl_hours` | - | - | - | 24 |
| Output Format | `output.formats` | `-f` | `--format` | - | both |
| Output Directory | `output.directory` | - | `--output-dir` | `GITHUB_ACTIVITY_OUTPUT_DIR` | ./reports |
| Log Level | `logging.level` | - | `--log-level` | `GITHUB_ACTIVITY_LOG_LEVEL` | INFO |
| Log Directory | `logging.file.directory` | - | - | `GITHUB_ACTIVITY_LOG_DIR` | ./logs |
| Log Retention | `logging.file.cleanup.retention_days` | - | - | - | 30 |
| Error Log Max Size | `logging.file.cleanup.error_log.max_size_mb` | - | - | - | 10 |
| Report Retention | `output_cleanup.retention_years` | - | - | - | 2 |
| Keep Versions | `output_cleanup.keep_versions` | - | - | - | 3 |

---

## 3. Feature Specifications

Each feature section follows the pattern:
1. **Specification** - Defines WHAT (settings table)
2. **Configuration** - Shows HOW in config.yaml
3. **Implementation** - Shows CODE (dataclass/functions)
4. **Validation Checklist** - Verifies consistency

---

### 3.1 CLI Interface

#### 3.1.1 Specification

| Option | Short | Long | Type | Default | Description |
|--------|-------|------|------|---------|-------------|
| Month | `-m` | `--month` | int (1-12) | current month | Generate monthly report |
| Quarter | `-q` | `--quarter` | int (1-4) | current quarter | Generate quarterly report |
| Year | `-y` | `--year` | int | current year | Report year |
| User | `-u` | `--user` | string | gh logged-in user | GitHub username |
| Format | `-f` | `--format` | enum | both | json, markdown, or both |
| Log Level | - | `--log-level` | enum | INFO | DEBUG, INFO, WARNING, ERROR |
| Output Dir | `-o` | `--output-dir` | path | ./reports | Custom output path |
| No Cache | - | `--no-cache` | flag | false | Disable caching |
| Include Repos | - | `--include-repos` | string | - | Whitelist repos (comma-sep) |
| Exclude Repos | - | `--exclude-repos` | string | - | Blacklist repos (comma-sep) |
| Help | `-h` | `--help` | flag | - | Show help message |

**Mutual Exclusivity:** `-m/--month` and `-q/--quarter` cannot be used together.

**Smart Defaults:**
- No flags → Monthly report for current month
- `-q` alone → Quarterly report for current quarter
- `-q 2` → Quarterly report for Q2
- `-m` alone → Monthly report for current month
- `-m 6` → Monthly report for June

#### 3.1.2 Configuration

```yaml
# CLI defaults can be overridden in config.yaml
period:
  default_type: monthly  # monthly or quarterly
```

#### 3.1.3 Implementation

```python
# generate_report.py

import click
from datetime import datetime

def get_current_quarter() -> int:
    """Return current quarter (1-4) based on current month."""
    return (datetime.now().month - 1) // 3 + 1

def get_logged_in_user() -> str:
    """Get currently logged-in GitHub user from gh CLI."""
    result = subprocess.run(
        ["gh", "api", "/user", "--jq", ".login"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

@click.command()
@click.option("-m", "--month", type=click.IntRange(1, 12),
              default=None, help="Monthly report (1-12)")
@click.option("-q", "--quarter", type=click.IntRange(1, 4),
              default=None, help="Quarterly report (1-4)")
@click.option("-y", "--year", type=int,
              default=lambda: datetime.now().year, help="Report year")
@click.option("-u", "--user", type=str,
              default=None, help="GitHub username")
@click.option("-f", "--format", "output_format",
              type=click.Choice(["json", "markdown", "both"]),
              default="both", help="Output format")
@click.option("--log-level",
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
              default=None, help="Log level (default: from config)")
@click.option("-o", "--output-dir", type=click.Path(),
              default="reports", help="Output directory")
@click.option("--no-cache", is_flag=True,
              help="Disable caching")
@click.option("--include-repos", type=str,
              default=None, help="Whitelist repos (comma-separated)")
@click.option("--exclude-repos", type=str,
              default=None, help="Blacklist repos (comma-separated)")
def main(month, quarter, year, user, output_format,
         log_level, output_dir, no_cache, include_repos, exclude_repos):
    """Generate GitHub activity report."""

    # Validate mutual exclusivity
    if month is not None and quarter is not None:
        raise click.UsageError("Cannot use --month and --quarter together")

    # Apply smart defaults  # UC-2.1 | PLAN-3.1
    username = user if user else get_logged_in_user()

    if month is None and quarter is None:
        month = datetime.now().month  # Default to current month

    # Determine period type
    if quarter is not None:
        period_type = "quarterly"
        period_value = quarter
    else:
        period_type = "monthly"
        period_value = month

    # Parse repo filters
    repos_include = include_repos.split(",") if include_repos else []
    repos_exclude = exclude_repos.split(",") if exclude_repos else []

    # ... rest of implementation
```

#### 3.1.4 Validation Checklist

- [ ] All short options in spec match `@click.option` short param
- [ ] All long options in spec match `@click.option` long param
- [ ] All defaults in spec match `@click.option` default param
- [ ] All types in spec match `@click.option` type param
- [ ] Mutual exclusivity enforced in code
- [ ] Smart defaults implemented as specified

---

### 3.2 User Settings

#### 3.2.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `username` | string \| null | null (auto-detect) | GitHub username |
| `organizations` | list[string] | [] (all) | Organizations to include |

**Auto-detection:** When `username` is null, detect via `gh api /user --jq .login`

#### 3.2.2 Configuration

```yaml
user:
  # GitHub username (default: auto-detected from gh CLI)
  # Override: -u/--user or GITHUB_ACTIVITY_USER env var
  username: null  # null = use logged-in gh user

  # Organizations to include (default: all accessible)
  # Config-only setting (no CLI option)
  organizations: []  # empty = all orgs
```

#### 3.2.3 Implementation

```python
# src/config/settings.py

from dataclasses import dataclass, field

@dataclass
class UserConfig:
    """User configuration settings."""
    username: str | None = None           # null = auto-detect
    organizations: list[str] = field(default_factory=list)  # empty = all

    def get_username(self) -> str:
        """Get username, auto-detecting if not set."""
        if self.username is None:
            return get_logged_in_user()
        return self.username

    def get_organizations(self) -> list[str] | None:
        """Get organizations, returning None for 'all'."""
        return self.organizations if self.organizations else None
```

#### 3.2.4 Validation Checklist

- [ ] `UserConfig.username` default matches spec (None)
- [ ] `UserConfig.organizations` default matches spec (empty list)
- [ ] Config.yaml `user.username` default matches spec (null)
- [ ] Config.yaml `user.organizations` default matches spec (empty)
- [ ] Auto-detection logic implemented

---

### 3.3 Repository Filters

#### 3.3.1 Specification

| Setting | Type | Default | CLI | Description |
|---------|------|---------|-----|-------------|
| `include_private` | bool | true | - | Include private repositories |
| `include_forks` | bool | false | - | Include forked repositories |
| `include` | list[string] | [] | `--include-repos` | Whitelist repos (owner/repo) |
| `exclude` | list[string] | [] | `--exclude-repos` | Blacklist repos (owner/repo) |

#### 3.3.2 Configuration

```yaml
repositories:
  # Include private repositories (config-only)
  include_private: true

  # Include forked repositories (config-only)
  include_forks: false

  # Include specific repositories (whitelist) - owner/repo format
  # CLI: --include-repos
  include: []

  # Exclude specific repositories (blacklist) - owner/repo format
  # CLI: --exclude-repos
  exclude: []
```

#### 3.3.3 Implementation

```python
# src/config/settings.py

@dataclass
class RepositoryConfig:
    """Repository filter configuration."""
    include_private: bool = True
    include_forks: bool = False
    include: list[str] = field(default_factory=list)  # whitelist
    exclude: list[str] = field(default_factory=list)  # blacklist

    def should_include(self, repo: dict) -> bool:
        """Check if a repository should be included."""
        full_name = repo.get("full_name", "")

        # If whitelist is set, repo must be in it
        if self.include and full_name not in self.include:
            return False

        # Check exclusion list (blacklist)
        if full_name in self.exclude:
            return False

        # Check private filter
        if repo.get("private", False) and not self.include_private:
            return False

        # Check fork filter
        if repo.get("fork", False) and not self.include_forks:
            return False

        return True
```

#### 3.3.4 Validation Checklist

- [ ] `RepositoryConfig.include_private` default matches spec (True)
- [ ] `RepositoryConfig.include_forks` default matches spec (False)
- [ ] `RepositoryConfig.include` default matches spec (empty list)
- [ ] `RepositoryConfig.exclude` default matches spec (empty list)
- [ ] Config.yaml values match spec defaults
- [ ] CLI `--include-repos` passes to `repositories.include`
- [ ] CLI `--exclude-repos` passes to `repositories.exclude`

---

### 3.4 Fetching Strategy

#### 3.4.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `high_activity_threshold` | int | 100 | Events per week before switching to daily |
| `request_delay` | float | 1.0 | Pause between API requests (seconds) |
| `max_retries` | int | 3 | Maximum retries on failure |
| `backoff_base` | float | 2.0 | Exponential backoff base (seconds) |
| `timeout` | int | 30 | Request timeout (seconds) |

**Adaptive Fetching Algorithm:**
1. Split period into weeks (7-day chunks)
2. Fetch each week's data
3. If week has >= `high_activity_threshold` events, re-fetch day-by-day
4. Merge and deduplicate results

#### 3.4.2 Configuration

```yaml
fetching:
  # Threshold for switching from weekly to daily fetching
  # If a week returns >= this many events, re-fetch day by day
  high_activity_threshold: 100

  # Pause between API requests (seconds)
  request_delay: 1.0

  # Maximum retries on failure
  max_retries: 3

  # Exponential backoff base (seconds)
  backoff_base: 2.0

  # Request timeout (seconds)
  timeout: 30
```

#### 3.4.3 Implementation

```python
# src/config/settings.py

@dataclass
class FetchingConfig:
    """Fetching strategy configuration."""
    high_activity_threshold: int = 100
    request_delay: float = 1.0
    max_retries: int = 3
    backoff_base: float = 2.0
    timeout: int = 30


# src/fetchers/base.py

from datetime import date, timedelta
from typing import Iterator

class BaseFetcher:
    """Base class for all data fetchers."""

    def __init__(self, config: FetchingConfig, logger: Logger):
        self.config = config
        self.logger = logger

    def fetch_period(self, start_date: date, end_date: date) -> list[dict]:
        """
        Fetch data for a period using adaptive granularity.
        """
        all_events = []

        for week_start, week_end in self._iter_weeks(start_date, end_date):
            # First attempt: fetch entire week
            week_events = self._fetch_range(week_start, week_end)

            if len(week_events) >= self.config.high_activity_threshold:
                # High activity detected - fetch day by day
                self.logger.info(
                    f"High activity week ({len(week_events)} events), "
                    f"switching to daily fetching"
                )
                week_events = self._fetch_week_by_days(week_start, week_end)

            all_events.extend(week_events)
            self._rate_limit_pause()

        return self._deduplicate(all_events)

    def _iter_weeks(self, start: date, end: date) -> Iterator[tuple[date, date]]:
        """Iterate through weeks, handling partial weeks at boundaries."""
        current = start
        while current <= end:
            week_end = min(current + timedelta(days=6), end)
            yield (current, week_end)
            current = week_end + timedelta(days=1)

    def _fetch_week_by_days(self, week_start: date, week_end: date) -> list[dict]:
        """Fetch a high-activity week day by day."""
        daily_events = []
        current = week_start

        while current <= week_end:
            day_events = self._fetch_range(current, current)
            daily_events.extend(day_events)
            self._rate_limit_pause()
            current += timedelta(days=1)

        return daily_events

    def _rate_limit_pause(self):
        """Pause between requests to respect rate limits."""
        time.sleep(self.config.request_delay)

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch data for a date range. Override in subclasses."""
        raise NotImplementedError

    def _deduplicate(self, events: list[dict]) -> list[dict]:
        """Remove duplicate events based on unique identifier."""
        seen = set()
        unique = []
        for event in events:
            event_id = self._get_event_id(event)
            if event_id not in seen:
                seen.add(event_id)
                unique.append(event)
        return unique

    def _get_event_id(self, event: dict) -> str:
        """Get unique identifier for an event. Override in subclasses."""
        raise NotImplementedError
```

#### 3.4.4 Validation Checklist

- [ ] `FetchingConfig.high_activity_threshold` default matches spec (100)
- [ ] `FetchingConfig.request_delay` default matches spec (1.0)
- [ ] `FetchingConfig.max_retries` default matches spec (3)
- [ ] `FetchingConfig.backoff_base` default matches spec (2.0)
- [ ] `FetchingConfig.timeout` default matches spec (30)
- [ ] Config.yaml values match spec defaults
- [ ] `fetch_period()` uses `high_activity_threshold` correctly
- [ ] `_rate_limit_pause()` uses `request_delay` correctly

---

### 3.5 Caching

#### 3.5.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | bool | true | Enable response caching |
| `directory` | string | .cache | Cache directory path |
| `ttl_hours` | int | 24 | Cache time-to-live (hours) |

#### 3.5.2 Configuration

```yaml
cache:
  # Enable response caching
  enabled: true

  # Cache directory (relative to script or absolute path)
  directory: .cache

  # Cache time-to-live (hours)
  ttl_hours: 24
```

#### 3.5.3 Implementation

```python
# src/config/settings.py

@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True
    directory: str = ".cache"
    ttl_hours: int = 24

    @property
    def ttl_seconds(self) -> int:
        """Get TTL in seconds."""
        return self.ttl_hours * 3600


# src/utils/cache.py

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class ResponseCache:
    """Simple file-based response cache."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_dir = Path(config.directory)
        if config.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict | None:
        """Get cached response if valid."""
        if not self.config.enabled:
            return None

        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None

        # Check TTL
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(seconds=self.config.ttl_seconds):
            cache_file.unlink()
            return None

        with open(cache_file, "r") as f:
            return json.load(f)

    def set(self, key: str, data: dict):
        """Store response in cache."""
        if not self.config.enabled:
            return

        cache_file = self._get_cache_path(key)
        with open(cache_file, "w") as f:
            json.dump(data, f)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
```

#### 3.5.4 Validation Checklist

- [ ] `CacheConfig.enabled` default matches spec (True)
- [ ] `CacheConfig.directory` default matches spec (".cache")
- [ ] `CacheConfig.ttl_hours` default matches spec (24)
- [ ] Config.yaml values match spec defaults
- [ ] CLI `--no-cache` sets `enabled` to False

---

### 3.6 Output & Reports

#### 3.6.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `directory` | string | reports | Output directory path |
| `formats` | list[enum] | [json, markdown] | Output formats |
| `include_links` | bool | true | Include GitHub links in markdown |
| `commit_message_format` | enum | truncated | full, first_line, truncated |

**File Naming Convention:**
| Period Type | Pattern | Example |
|-------------|---------|---------|
| Monthly | `{year}-{MM}-github-activity-{n}.md` | `2024-12-github-activity-1.md` |
| Quarterly | `{year}-Q{Q}-github-activity-{n}.md` | `2024-Q4-github-activity-1.md` |

**Increment Logic:** If file exists, increment `{n}` (e.g., `-1`, `-2`, `-3`)

#### 3.6.2 Configuration

```yaml
output:
  # Output directory for reports (relative to script or absolute path)
  directory: reports

  # Output formats: json, markdown, or both
  formats:
    - json
    - markdown

  # Include GitHub links in markdown report
  include_links: true

  # Commit message format: full, first_line, or truncated (100 chars)
  commit_message_format: truncated
```

#### 3.6.3 Implementation

```python
# src/config/settings.py

from typing import Literal

@dataclass
class OutputConfig:
    """Output configuration."""
    directory: str = "reports"
    formats: list[str] = field(default_factory=lambda: ["json", "markdown"])
    include_links: bool = True
    commit_message_format: Literal["full", "first_line", "truncated"] = "truncated"


# src/utils/file_utils.py

from pathlib import Path
from calendar import monthrange
from typing import Literal

def get_next_filename(
    base_dir: Path,
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> Path:
    """
    Get next available filename, incrementing if exists.

    Monthly pattern: {year}-{month:02d}-github-activity-{n}.md
    Quarterly pattern: {year}-Q{quarter}-github-activity-{n}.md
    """
    year_dir = base_dir / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    if period_type == "monthly":
        pattern = f"{year}-{period_value:02d}-github-activity-*.md"
        prefix = f"{year}-{period_value:02d}-github-activity"
    else:
        pattern = f"{year}-Q{period_value}-github-activity-*.md"
        prefix = f"{year}-Q{period_value}-github-activity"

    existing = sorted(year_dir.glob(pattern))

    if not existing:
        return year_dir / f"{prefix}-1.md"

    # Extract last number and increment
    last_file = existing[-1]
    last_num = int(last_file.stem.split("-")[-1])
    return year_dir / f"{prefix}-{last_num + 1}.md"


def get_period_dates(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> tuple[str, str]:
    """
    Get start and end dates for a period.

    Returns (start_date, end_date) as YYYY-MM-DD strings.
    """
    if period_type == "monthly":
        _, last_day = monthrange(year, period_value)
        return (
            f"{year}-{period_value:02d}-01",
            f"{year}-{period_value:02d}-{last_day:02d}"
        )
    else:
        quarters = {
            1: (f"{year}-01-01", f"{year}-03-31"),
            2: (f"{year}-04-01", f"{year}-06-30"),
            3: (f"{year}-07-01", f"{year}-09-30"),
            4: (f"{year}-10-01", f"{year}-12-31"),
        }
        return quarters[period_value]
```

#### 3.6.4 Validation Checklist

- [ ] `OutputConfig.directory` default matches spec ("reports")
- [ ] `OutputConfig.formats` default matches spec (["json", "markdown"])
- [ ] `OutputConfig.include_links` default matches spec (True)
- [ ] `OutputConfig.commit_message_format` default matches spec ("truncated")
- [ ] Config.yaml values match spec defaults
- [ ] `get_next_filename()` produces correct monthly pattern
- [ ] `get_next_filename()` produces correct quarterly pattern
- [ ] `get_period_dates()` returns correct date ranges

---

### 3.7 Metrics

#### 3.7.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `pr_metrics` | bool | true | Calculate PR metrics |
| `review_metrics` | bool | true | Calculate review metrics |
| `engagement_metrics` | bool | true | Calculate engagement metrics |
| `productivity_patterns` | bool | true | Calculate productivity by day/hour |
| `reaction_breakdown` | bool | true | Include reaction emoji breakdown |

**PR Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| `avg_commits_per_pr` | sum(commits) / count(prs) |
| `avg_time_to_merge_hours` | avg(merged_at - created_at) |
| `avg_time_to_first_review_hours` | avg(first_review_at - created_at) |
| `avg_review_iterations` | avg(count of review rounds per PR) |
| `prs_merged_without_changes` | count(prs approved on first review) |
| `prs_with_requested_changes` | count(prs with "changes_requested") |

**Review Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| `avg_review_turnaround_hours` | avg(review_submitted_at - review_requested_at) |
| `reviews_with_comments` | count(reviews where body.length > 0) |
| `approvals` | count(reviews where state == "APPROVED") |
| `changes_requested` | count(reviews where state == "CHANGES_REQUESTED") |

**Engagement Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| `avg_response_time_hours` | avg(time between comment and reply) |
| `comment_to_code_ratio` | total_comments / total_commits |
| `collaboration_score` | weighted(reviews + comments + reactions) |

#### 3.7.2 Configuration

```yaml
metrics:
  # Calculate PR metrics (time to merge, commits per PR, etc.)
  pr_metrics: true

  # Calculate review metrics (turnaround time, approval rate)
  review_metrics: true

  # Calculate engagement metrics (response time, collaboration score)
  engagement_metrics: true

  # Calculate productivity patterns (by day of week, by hour)
  productivity_patterns: true

  # Include reaction emoji breakdown
  reaction_breakdown: true
```

#### 3.7.3 Implementation

```python
# src/config/settings.py

@dataclass
class MetricsConfig:
    """Metrics calculation configuration."""
    pr_metrics: bool = True
    review_metrics: bool = True
    engagement_metrics: bool = True
    productivity_patterns: bool = True
    reaction_breakdown: bool = True


# src/processors/metrics.py

from dataclasses import dataclass
from datetime import datetime

@dataclass
class PRMetrics:
    """Calculated PR metrics."""
    avg_commits_per_pr: float = 0.0
    avg_time_to_merge_hours: float = 0.0
    avg_time_to_first_review_hours: float = 0.0
    avg_review_iterations: float = 0.0
    prs_merged_without_changes: int = 0
    prs_with_requested_changes: int = 0


@dataclass
class ReviewMetrics:
    """Calculated review metrics."""
    avg_review_turnaround_hours: float = 0.0
    reviews_with_comments: int = 0
    approvals: int = 0
    changes_requested: int = 0


@dataclass
class EngagementMetrics:
    """Calculated engagement metrics."""
    avg_response_time_hours: float = 0.0
    comment_to_code_ratio: float = 0.0
    collaboration_score: float = 0.0


class MetricsCalculator:
    """Calculate advanced metrics from activity data."""

    def __init__(self, config: MetricsConfig):
        self.config = config

    def calculate_pr_metrics(self, prs: list[dict]) -> PRMetrics | None:
        """Calculate PR-related metrics."""
        if not self.config.pr_metrics or not prs:
            return None

        metrics = PRMetrics()

        # Calculate averages
        total_commits = sum(pr.get("commits_count", 0) for pr in prs)
        metrics.avg_commits_per_pr = total_commits / len(prs)

        # Time to merge
        merge_times = []
        for pr in prs:
            if pr.get("merged_at") and pr.get("created_at"):
                created = datetime.fromisoformat(pr["created_at"].rstrip("Z"))
                merged = datetime.fromisoformat(pr["merged_at"].rstrip("Z"))
                merge_times.append((merged - created).total_seconds() / 3600)

        if merge_times:
            metrics.avg_time_to_merge_hours = sum(merge_times) / len(merge_times)

        return metrics

    def calculate_review_metrics(self, reviews: list[dict]) -> ReviewMetrics | None:
        """Calculate review-related metrics."""
        if not self.config.review_metrics or not reviews:
            return None

        metrics = ReviewMetrics()
        metrics.reviews_with_comments = sum(
            1 for r in reviews if r.get("body_length", 0) > 0
        )
        metrics.approvals = sum(
            1 for r in reviews if r.get("state") == "APPROVED"
        )
        metrics.changes_requested = sum(
            1 for r in reviews if r.get("state") == "CHANGES_REQUESTED"
        )

        return metrics

    def calculate_engagement_metrics(
        self,
        commits: list[dict],
        comments: list[dict]
    ) -> EngagementMetrics | None:
        """Calculate engagement-related metrics."""
        if not self.config.engagement_metrics:
            return None

        metrics = EngagementMetrics()

        if commits:
            metrics.comment_to_code_ratio = len(comments) / len(commits)

        return metrics

    def calculate_productivity_patterns(
        self,
        events: list[dict]
    ) -> dict | None:
        """Calculate productivity by day of week and hour."""
        if not self.config.productivity_patterns or not events:
            return None

        by_day = {day: 0 for day in [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]}
        by_hour = {str(h): 0 for h in range(24)}

        for event in events:
            if "created_at" in event:
                dt = datetime.fromisoformat(event["created_at"].rstrip("Z"))
                day_name = dt.strftime("%A")
                hour = str(dt.hour)
                by_day[day_name] += 1
                by_hour[hour] += 1

        return {
            "by_day": by_day,
            "by_hour": by_hour
        }
```

#### 3.7.4 Validation Checklist

- [ ] `MetricsConfig.pr_metrics` default matches spec (True)
- [ ] `MetricsConfig.review_metrics` default matches spec (True)
- [ ] `MetricsConfig.engagement_metrics` default matches spec (True)
- [ ] `MetricsConfig.productivity_patterns` default matches spec (True)
- [ ] `MetricsConfig.reaction_breakdown` default matches spec (True)
- [ ] Config.yaml values match spec defaults
- [ ] All PR metrics from spec are calculated
- [ ] All review metrics from spec are calculated
- [ ] All engagement metrics from spec are calculated

---

### 3.8 Logging

#### 3.8.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `level` | enum | INFO | DEBUG, INFO, WARNING, ERROR, TRACE |
| `colorize` | bool | true | Colorized console output |
| `show_timestamps` | bool | true | Show timestamps in console |
| `progress_style` | enum | rich | rich, simple, none |
| `file.enabled` | bool | true | Enable file logging |
| `file.directory` | string | logs | Log directory |
| `file.organize_by_date` | bool | true | Organize logs by year/month |
| `file.timestamp_format` | string | %Y-%m-%d_%H%M%S | Timestamp format for filenames |
| `file.format` | enum | jsonl | jsonl, text |
| `file.separate_errors` | bool | true | Separate error log file |
| `file.error_file` | string | errors.log | Error log filename |
| `file.performance_log` | bool | true | Enable performance logging |
| `performance.log_api_calls` | bool | true | Log API request/response |
| `performance.log_timing` | bool | true | Log operation timing |
| `performance.slow_threshold_ms` | int | 1000 | Warn if operation exceeds |

**Log File Organization:**
```
logs/
├── {year}/
│   └── {month}/
│       ├── {date}_{time}_activity.log
│       └── {date}_{time}_performance.log
├── errors/
│   └── errors_{timestamp}.log.gz  (rotated)
└── errors.log  (active)
```

**Log Entry Fields:**
| Field | Level | Description |
|-------|-------|-------------|
| `timestamp` | all | ISO 8601 timestamp |
| `level` | all | Log level |
| `module` | all | Source module name |
| `message` | all | Log message |
| `duration_ms` | DEBUG | Operation duration |
| `items_processed` | DEBUG | Count of items |
| `rate_limit_remaining` | INFO | API quota (when < 20%) |

#### 3.8.2 Configuration

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, TRACE
  level: INFO

  # Colorized console output
  colorize: true

  # Show timestamps in console
  show_timestamps: true

  # Progress bar style: rich, simple, none
  progress_style: rich

  # File logging
  file:
    enabled: true
    directory: logs
    organize_by_date: true
    timestamp_format: "%Y-%m-%d_%H%M%S"
    format: jsonl
    separate_errors: true
    error_file: errors.log
    performance_log: true

  # What to include in logs
  include:
    timestamps: true
    module_name: true
    line_numbers: false  # true in DEBUG mode
    stack_traces: false  # true on errors

  # Performance logging
  performance:
    log_api_calls: true
    log_timing: true
    log_memory: false  # true in TRACE mode
    slow_threshold_ms: 1000  # warn if operation > 1s
```

#### 3.8.3 Implementation

```python
# src/config/settings.py

@dataclass
class LogFileConfig:
    """Log file configuration."""
    enabled: bool = True
    directory: str = "logs"
    organize_by_date: bool = True
    timestamp_format: str = "%Y-%m-%d_%H%M%S"
    format: Literal["jsonl", "text"] = "jsonl"
    separate_errors: bool = True
    error_file: str = "errors.log"
    performance_log: bool = True


@dataclass
class LogPerformanceConfig:
    """Performance logging configuration."""
    log_api_calls: bool = True
    log_timing: bool = True
    log_memory: bool = False
    slow_threshold_ms: int = 1000


@dataclass
class LoggingConfig:
    """Complete logging configuration."""
    level: str = "INFO"
    colorize: bool = True
    show_timestamps: bool = True
    progress_style: Literal["rich", "simple", "none"] = "rich"
    file: LogFileConfig = field(default_factory=LogFileConfig)
    performance: LogPerformanceConfig = field(default_factory=LogPerformanceConfig)


# src/utils/logger.py

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

class StructuredLogger:
    """Structured logger with performance tracking and context."""

    def __init__(self, name: str, config: LoggingConfig):
        self.name = name
        self.config = config
        self._context: dict[str, Any] = {}
        self._timers: dict[str, datetime] = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Configure logging handlers based on config."""
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(getattr(logging, self.config.level))

        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(self._get_console_formatter())
        self._logger.addHandler(console)

        # File handler
        if self.config.file.enabled:
            log_path = self._get_log_path()
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(self._get_file_formatter())
            self._logger.addHandler(file_handler)

            # Separate error file
            if self.config.file.separate_errors:
                error_path = Path(self.config.file.directory) / self.config.file.error_file
                error_handler = logging.FileHandler(error_path)
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(self._get_file_formatter())
                self._logger.addHandler(error_handler)

    def _get_log_path(self) -> Path:
        """Get log file path based on config."""
        base_dir = Path(self.config.file.directory)

        if self.config.file.organize_by_date:
            now = datetime.now()
            log_dir = base_dir / str(now.year) / f"{now.month:02d}"
        else:
            log_dir = base_dir

        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(self.config.file.timestamp_format)
        return log_dir / f"{timestamp}_activity.log"

    def _get_console_formatter(self) -> logging.Formatter:
        """Get formatter for console output."""
        fmt = ""
        if self.config.show_timestamps:
            fmt += "%(asctime)s "
        fmt += "[%(levelname)s] %(name)s: %(message)s"
        return logging.Formatter(fmt)

    def _get_file_formatter(self) -> logging.Formatter:
        """Get formatter for file output."""
        if self.config.file.format == "jsonl":
            return JsonFormatter()
        return logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    def set_context(self, **kwargs):
        """Set persistent context for all log entries."""
        self._context.update(kwargs)

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self._timers[operation] = datetime.now()

    def end_timer(self, operation: str, **extra) -> float:
        """End timing and log the duration."""
        if operation not in self._timers:
            return 0.0

        duration = (datetime.now() - self._timers[operation]).total_seconds()
        duration_ms = int(duration * 1000)

        del self._timers[operation]

        if self.config.performance.log_timing:
            self.debug(f"{operation} completed", duration_ms=duration_ms, **extra)

        if duration_ms > self.config.performance.slow_threshold_ms:
            self.warning(f"{operation} slow", duration_ms=duration_ms, **extra)

        return duration

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs):
        """Log with context and extra fields."""
        extra = {**self._context, **kwargs}
        self._logger.log(level, msg, extra={"structured": extra})


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "structured"):
            log_obj.update(record.structured)

        return json.dumps(log_obj)
```

#### 3.8.4 Validation Checklist

- [ ] `LoggingConfig.level` default matches spec ("INFO")
- [ ] `LoggingConfig.colorize` default matches spec (True)
- [ ] `LoggingConfig.show_timestamps` default matches spec (True)
- [ ] `LoggingConfig.progress_style` default matches spec ("rich")
- [ ] `LogFileConfig.enabled` default matches spec (True)
- [ ] `LogFileConfig.directory` default matches spec ("logs")
- [ ] `LogFileConfig.organize_by_date` default matches spec (True)
- [ ] `LogFileConfig.timestamp_format` default matches spec
- [ ] `LogFileConfig.format` default matches spec ("jsonl")
- [ ] `LogFileConfig.separate_errors` default matches spec (True)
- [ ] `LogFileConfig.error_file` default matches spec ("errors.log")
- [ ] `LogFileConfig.performance_log` default matches spec (True)
- [ ] `LogPerformanceConfig.slow_threshold_ms` default matches spec (1000)
- [ ] Config.yaml values match spec defaults
- [ ] Log file organization matches spec diagram
- [ ] All log entry fields from spec are included

---

### 3.9 Log Cleanup

#### 3.9.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `cleanup.trigger` | enum | startup | startup, shutdown, both, manual |
| `cleanup.retention_days` | int | 30 | Delete activity logs after N days |
| `cleanup.retention_days_performance` | int | 14 | Delete performance logs after N days |
| `cleanup.max_total_size_mb` | int | 500 | Max total size of all logs |
| `cleanup.max_file_size_mb` | int | 50 | Max size per log file |
| `cleanup.max_files` | int | 100 | Max number of log files |
| `cleanup.keep_minimum_days` | int | 7 | Always keep at least N days |
| `cleanup.strategy` | enum | oldest_first | oldest_first, largest_first |
| `cleanup.error_log.max_size_mb` | int | 10 | Rotate error log when exceeded |
| `cleanup.error_log.max_files` | int | 50 | Keep max N rotated error logs |
| `cleanup.error_log.max_age_days` | int | 365 | Delete error logs older than N days |
| `cleanup.error_log.compress_rotated` | bool | true | Compress rotated error logs |

**Error Log Rotation Process:**
```
When errors.log > 10MB:
1. Move to errors/: errors.log → errors/errors_{timestamp}.log
2. Compress: errors/errors_{timestamp}.log → errors/errors_{timestamp}.log.gz
3. Create new: errors.log (empty)
```

#### 3.9.2 Configuration

```yaml
logging:
  file:
    # ... other file settings ...

    cleanup:
      trigger: startup                    # startup, shutdown, both, manual
      retention_days: 30                  # Delete activity logs after 30 days
      retention_days_performance: 14      # Performance logs shorter retention
      max_total_size_mb: 500              # Max total size of all logs
      max_file_size_mb: 50                # Max size per log file
      max_files: 100                      # Max number of log files
      keep_minimum_days: 7                # Always keep at least 7 days
      strategy: oldest_first              # oldest_first, largest_first

      error_log:
        max_size_mb: 10                   # Rotate when > 10MB
        max_files: 50                     # Keep max 50 rotated files
        max_age_days: 365                 # Delete error logs older than 1 year
        compress_rotated: true            # Compress rotated logs (.gz)
```

#### 3.9.3 Implementation

```python
# src/config/settings.py

@dataclass
class ErrorLogCleanupConfig:
    """Error log rotation configuration."""
    max_size_mb: int = 10
    max_files: int = 50
    max_age_days: int = 365
    compress_rotated: bool = True


@dataclass
class LogCleanupConfig:
    """Log cleanup configuration."""
    trigger: Literal["startup", "shutdown", "both", "manual"] = "startup"
    retention_days: int = 30
    retention_days_performance: int = 14
    max_total_size_mb: int = 500
    max_file_size_mb: int = 50
    max_files: int = 100
    keep_minimum_days: int = 7
    strategy: Literal["oldest_first", "largest_first"] = "oldest_first"
    error_log: ErrorLogCleanupConfig = field(default_factory=ErrorLogCleanupConfig)


# src/utils/log_cleanup.py

from pathlib import Path
from datetime import datetime, timedelta
import gzip
import shutil

class LogCleaner:
    """Automatic log cleanup based on configurable thresholds."""

    def __init__(self, logs_dir: Path, config: LogCleanupConfig):
        self.logs_dir = logs_dir
        self.config = config
        self.stats = {"deleted": 0, "archived": 0, "freed_mb": 0.0}

    def cleanup(self) -> dict:
        """Run all cleanup operations and return statistics."""
        self._cleanup_by_age()
        self._cleanup_by_size()
        self._cleanup_by_count()
        self._handle_error_log()
        self._remove_empty_directories()
        return self.stats

    def _cleanup_by_age(self):
        """Delete logs older than retention threshold."""
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        cutoff_perf = datetime.now() - timedelta(
            days=self.config.retention_days_performance
        )
        minimum_cutoff = datetime.now() - timedelta(
            days=self.config.keep_minimum_days
        )

        for log_file in self.logs_dir.rglob("*.log"):
            if log_file.name == "errors.log":
                continue

            file_date = self._parse_date_from_filename(log_file)
            if not file_date or file_date >= minimum_cutoff:
                continue

            threshold = cutoff_perf if "_performance.log" in log_file.name else cutoff

            if file_date < threshold:
                self._delete_file(log_file)

    def _cleanup_by_size(self):
        """Delete logs if total size exceeds threshold."""
        max_bytes = self.config.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.config.max_file_size_mb * 1024 * 1024

        # Handle oversized individual files
        for log_file in self.logs_dir.rglob("*.log"):
            if log_file.name == "errors.log":
                continue
            if log_file.stat().st_size > max_file_bytes:
                self._delete_file(log_file)

        # Check total size
        total_size = sum(
            f.stat().st_size
            for f in self.logs_dir.rglob("*.log")
            if f.name != "errors.log"
        )

        if total_size > max_bytes:
            self._free_space_by_strategy(total_size - max_bytes)

    def _cleanup_by_count(self):
        """Delete logs if file count exceeds threshold."""
        log_files = sorted(
            [f for f in self.logs_dir.rglob("*.log") if f.name != "errors.log"],
            key=lambda f: f.stat().st_mtime
        )

        while len(log_files) > self.config.max_files:
            oldest = log_files.pop(0)
            self._delete_file(oldest)

    def _handle_error_log(self):
        """Handle error log rotation by size with timestamp."""
        errors_dir = self.logs_dir / "errors"
        errors_dir.mkdir(exist_ok=True)

        current_log = self.logs_dir / "errors.log"
        if not current_log.exists():
            current_log.touch()
            return

        max_bytes = self.config.error_log.max_size_mb * 1024 * 1024

        if current_log.stat().st_size > max_bytes:
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            rotated_name = f"errors_{timestamp}.log"
            rotated_path = errors_dir / rotated_name

            # Move current log to errors/ directory
            shutil.move(current_log, rotated_path)

            # Compress if enabled
            if self.config.error_log.compress_rotated:
                with open(rotated_path, "rb") as f_in:
                    with gzip.open(f"{rotated_path}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                rotated_path.unlink()

            self.stats["archived"] += 1

            # Create new empty error log
            current_log.touch()

        # Cleanup old error logs
        self._cleanup_old_error_logs(errors_dir)

    def _cleanup_old_error_logs(self, errors_dir: Path):
        """Delete old rotated error logs based on age and count."""
        error_files = sorted(
            list(errors_dir.glob("errors_*.log*")),
            key=lambda f: f.stat().st_mtime
        )

        # Delete by age
        cutoff = datetime.now() - timedelta(days=self.config.error_log.max_age_days)
        for f in error_files[:]:
            try:
                date_str = f.stem.replace("errors_", "").split(".")[0]
                file_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink()
                    error_files.remove(f)
                    self.stats["deleted"] += 1
            except (ValueError, IndexError):
                pass

        # Delete by count
        while len(error_files) > self.config.error_log.max_files:
            oldest = error_files.pop(0)
            oldest.unlink()
            self.stats["deleted"] += 1

    def _free_space_by_strategy(self, bytes_to_free: int):
        """Free up space using configured strategy."""
        log_files = [
            f for f in self.logs_dir.rglob("*.log")
            if f.name != "errors.log"
        ]

        if self.config.strategy == "oldest_first":
            log_files.sort(key=lambda f: f.stat().st_mtime)
        elif self.config.strategy == "largest_first":
            log_files.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for log_file in log_files:
            if freed >= bytes_to_free:
                break
            freed += log_file.stat().st_size
            self._delete_file(log_file)

    def _delete_file(self, file_path: Path):
        """Delete a file and update stats."""
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_path.unlink()
        self.stats["deleted"] += 1
        self.stats["freed_mb"] += size_mb

    def _parse_date_from_filename(self, file_path: Path) -> datetime | None:
        """Parse date from log filename."""
        try:
            date_str = file_path.stem.split("_")[0]
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, IndexError):
            return None

    def _remove_empty_directories(self):
        """Remove empty log directories."""
        for dir_path in sorted(self.logs_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
```

#### 3.9.4 Validation Checklist

- [ ] `LogCleanupConfig.trigger` default matches spec ("startup")
- [ ] `LogCleanupConfig.retention_days` default matches spec (30)
- [ ] `LogCleanupConfig.retention_days_performance` default matches spec (14)
- [ ] `LogCleanupConfig.max_total_size_mb` default matches spec (500)
- [ ] `LogCleanupConfig.max_file_size_mb` default matches spec (50)
- [ ] `LogCleanupConfig.max_files` default matches spec (100)
- [ ] `LogCleanupConfig.keep_minimum_days` default matches spec (7)
- [ ] `LogCleanupConfig.strategy` default matches spec ("oldest_first")
- [ ] `ErrorLogCleanupConfig.max_size_mb` default matches spec (10)
- [ ] `ErrorLogCleanupConfig.max_files` default matches spec (50)
- [ ] `ErrorLogCleanupConfig.max_age_days` default matches spec (365)
- [ ] `ErrorLogCleanupConfig.compress_rotated` default matches spec (True)
- [ ] Config.yaml values match spec defaults
- [ ] Error log rotation follows spec process
- [ ] No symlinks used in implementation

---

### 3.10 Report Cleanup

#### 3.10.1 Specification

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | bool | true | Enable automatic cleanup |
| `trigger` | enum | startup | startup, shutdown, both, manual |
| `retention_years` | int | 2 | Keep reports for N years |
| `keep_versions` | int | 3 | Keep last N versions per period |
| `max_total_size_mb` | int | 1000 | Max total size of all reports |
| `max_file_size_mb` | int | 100 | Max size per report file |
| `max_reports` | int | 500 | Max number of report files |
| `keep_minimum_months` | int | 6 | Always keep at least N months |
| `strategy` | enum | oldest_first | oldest_first, largest_first |
| `archive.enabled` | bool | true | Archive old reports instead of delete |
| `archive.directory` | string | reports/archive | Archive location |
| `archive.compress` | bool | true | Compress archived reports |
| `archive.archive_after_days` | int | 365 | Archive reports older than N days |

**Version Cleanup Example:**
```
Period: 2024-12
Files: 2024-12-github-activity-1.md, -2.md, -3.md, -4.md, -5.md
keep_versions: 3
Result: Keep -3, -4, -5; Delete -1, -2
```

#### 3.10.2 Configuration

```yaml
output_cleanup:
  enabled: true
  trigger: startup
  retention_years: 2
  keep_versions: 3
  max_total_size_mb: 1000
  max_file_size_mb: 100
  max_reports: 500
  keep_minimum_months: 6
  strategy: oldest_first

  archive:
    enabled: true
    directory: reports/archive
    compress: true
    archive_after_days: 365
```

#### 3.10.3 Implementation

```python
# src/config/settings.py

@dataclass
class ArchiveConfig:
    """Archive configuration."""
    enabled: bool = True
    directory: str = "reports/archive"
    compress: bool = True
    archive_after_days: int = 365


@dataclass
class ReportCleanupConfig:
    """Report cleanup configuration."""
    enabled: bool = True
    trigger: Literal["startup", "shutdown", "both", "manual"] = "startup"
    retention_years: int = 2
    keep_versions: int = 3
    max_total_size_mb: int = 1000
    max_file_size_mb: int = 100
    max_reports: int = 500
    keep_minimum_months: int = 6
    strategy: Literal["oldest_first", "largest_first"] = "oldest_first"
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)


# src/utils/report_cleanup.py

from pathlib import Path
from datetime import datetime, timedelta
import gzip
import shutil
import re

class ReportCleaner:
    """Automatic report cleanup based on configurable thresholds."""

    # Pattern: 2024-12-github-activity-1.md or 2024-Q4-github-activity-2.json
    REPORT_PATTERN = re.compile(
        r"(\d{4})-(\d{2}|Q[1-4])-github-activity-(\d+)\.(md|json)"
    )

    def __init__(self, reports_dir: Path, config: ReportCleanupConfig):
        self.reports_dir = reports_dir
        self.config = config
        self.stats = {
            "deleted": 0,
            "archived": 0,
            "freed_mb": 0.0,
            "versions_cleaned": 0
        }

    def cleanup(self) -> dict:
        """Run all cleanup operations and return statistics."""
        if not self.config.enabled:
            return self.stats

        self._cleanup_old_versions()
        self._cleanup_by_age()
        self._archive_old_reports()
        self._cleanup_by_size()
        self._cleanup_by_count()
        self._remove_empty_directories()

        return self.stats

    def _cleanup_old_versions(self):
        """Keep only the last N versions of each period's report."""
        reports_by_period: dict[str, list[tuple[int, Path]]] = {}

        for report_file in self.reports_dir.rglob("*.*"):
            match = self.REPORT_PATTERN.match(report_file.name)
            if not match:
                continue

            year, period, version, ext = match.groups()
            period_key = f"{year}-{period}-{ext}"

            if period_key not in reports_by_period:
                reports_by_period[period_key] = []
            reports_by_period[period_key].append((int(version), report_file))

        # Delete old versions, keep only the last N
        for period_key, versions in reports_by_period.items():
            versions.sort(key=lambda x: x[0], reverse=True)

            for version_num, report_file in versions[self.config.keep_versions:]:
                self._delete_file(report_file)
                self.stats["versions_cleaned"] += 1

    def _cleanup_by_age(self):
        """Delete reports older than retention threshold."""
        cutoff = datetime.now() - timedelta(days=self.config.retention_years * 365)
        minimum_cutoff = datetime.now() - timedelta(
            days=self.config.keep_minimum_months * 30
        )

        for report_file in self._get_all_reports():
            file_date = self._get_report_date(report_file)
            if not file_date or file_date >= minimum_cutoff:
                continue

            if file_date < cutoff:
                self._delete_file(report_file)

    def _archive_old_reports(self):
        """Archive old reports instead of deleting."""
        if not self.config.archive.enabled:
            return

        cutoff = datetime.now() - timedelta(days=self.config.archive.archive_after_days)
        minimum_cutoff = datetime.now() - timedelta(
            days=self.config.keep_minimum_months * 30
        )
        archive_dir = Path(self.config.archive.directory)
        archive_dir.mkdir(parents=True, exist_ok=True)

        for report_file in self._get_all_reports():
            file_date = self._get_report_date(report_file)
            if not file_date or file_date >= minimum_cutoff:
                continue

            if file_date < cutoff:
                self._archive_file(report_file, archive_dir)

    def _archive_file(self, file_path: Path, archive_dir: Path):
        """Archive a single file."""
        if self.config.archive.compress:
            dest = archive_dir / f"{file_path.name}.gz"
            with open(file_path, "rb") as f_in:
                with gzip.open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            dest = archive_dir / file_path.name
            shutil.copy2(file_path, dest)

        file_path.unlink()
        self.stats["archived"] += 1

    def _cleanup_by_size(self):
        """Delete reports if total size exceeds threshold."""
        max_bytes = self.config.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.config.max_file_size_mb * 1024 * 1024

        # Handle oversized individual files
        for report_file in self._get_all_reports():
            if report_file.stat().st_size > max_file_bytes:
                self._delete_file(report_file)

        # Check total size
        total_size = sum(f.stat().st_size for f in self._get_all_reports())

        if total_size > max_bytes:
            self._free_space_by_strategy(total_size - max_bytes)

    def _cleanup_by_count(self):
        """Delete reports if count exceeds threshold."""
        reports = sorted(
            list(self._get_all_reports()),
            key=lambda f: f.stat().st_mtime
        )

        while len(reports) > self.config.max_reports:
            oldest = reports.pop(0)
            self._delete_file(oldest)

    def _free_space_by_strategy(self, bytes_to_free: int):
        """Free up space using configured strategy."""
        reports = list(self._get_all_reports())

        if self.config.strategy == "oldest_first":
            reports.sort(key=lambda f: f.stat().st_mtime)
        elif self.config.strategy == "largest_first":
            reports.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for report_file in reports:
            if freed >= bytes_to_free:
                break
            freed += report_file.stat().st_size
            self._delete_file(report_file)

    def _get_all_reports(self):
        """Get all report files."""
        for pattern in ["*.md", "*.json"]:
            yield from self.reports_dir.rglob(pattern)

    def _get_report_date(self, file_path: Path) -> datetime | None:
        """Extract date from report filename."""
        match = self.REPORT_PATTERN.match(file_path.name)
        if not match:
            return None

        year, period, _, _ = match.groups()
        try:
            if period.startswith("Q"):
                # Quarterly: use first month of quarter
                quarter = int(period[1])
                month = (quarter - 1) * 3 + 1
            else:
                month = int(period)
            return datetime(int(year), month, 1)
        except ValueError:
            return None

    def _delete_file(self, file_path: Path):
        """Delete a file and update stats."""
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_path.unlink()
        self.stats["deleted"] += 1
        self.stats["freed_mb"] += size_mb

    def _remove_empty_directories(self):
        """Remove empty report directories."""
        for dir_path in sorted(self.reports_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
```

#### 3.10.4 Validation Checklist

- [ ] `ReportCleanupConfig.enabled` default matches spec (True)
- [ ] `ReportCleanupConfig.trigger` default matches spec ("startup")
- [ ] `ReportCleanupConfig.retention_years` default matches spec (2)
- [ ] `ReportCleanupConfig.keep_versions` default matches spec (3)
- [ ] `ReportCleanupConfig.max_total_size_mb` default matches spec (1000)
- [ ] `ReportCleanupConfig.max_file_size_mb` default matches spec (100)
- [ ] `ReportCleanupConfig.max_reports` default matches spec (500)
- [ ] `ReportCleanupConfig.keep_minimum_months` default matches spec (6)
- [ ] `ReportCleanupConfig.strategy` default matches spec ("oldest_first")
- [ ] `ArchiveConfig.enabled` default matches spec (True)
- [ ] `ArchiveConfig.directory` default matches spec ("reports/archive")
- [ ] `ArchiveConfig.compress` default matches spec (True)
- [ ] `ArchiveConfig.archive_after_days` default matches spec (365)
- [ ] Config.yaml values match spec defaults
- [ ] Version cleanup keeps correct number of versions
- [ ] No symlinks used in implementation

---

## 4. Architecture

### 4.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW DIAGRAM                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   GitHub    │
                              │    API      │
                              └──────┬──────┘
                                     │
                                     ▼
┌──────────────┐            ┌─────────────────┐
│   User       │            │    gh CLI       │
│   Input      │───────────▶│   Commands      │
│  (month OR   │            │                 │
│   quarter,   │            │  - events API   │
│   year)      │            │  - search API   │
└──────────────┘            │  - graphQL API  │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Data Fetchers  │
                            │  (adaptive)     │
                            │                 │
                            │  Week → Day     │
                            │  fallback       │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   Aggregator    │
                            │                 │
                            │  - filter       │
                            │  - deduplicate  │
                            │  - calculate    │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   Validator     │
                            │                 │
                            │  - JSON schema  │
                            └────────┬────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │                               │
                     ▼                               ▼
            ┌─────────────────┐            ┌─────────────────┐
            │   JSON Report   │            │ Markdown Report │
            └─────────────────┘            └─────────────────┘
                     │                               │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  File System    │
                            │  reports/{year} │
                            └─────────────────┘
```

### 4.2 Module Structure

```
.scripts/github-activity/
│
├── docs/
│   ├── plan.md                   # Old plan (for verification)
│   └── plan-v2.md                # This document
│
├── reports/                      # Generated reports
│   └── {year}/
│       └── {username}/
│           ├── {year}-{MM}-github-activity-{n}.md
│           └── {year}-Q{Q}-github-activity-{n}.md
│
├── logs/                         # Log files
│   ├── {year}/{month}/
│   │   ├── {date}_{time}_activity.log
│   │   └── {date}_{time}_performance.log
│   ├── errors/
│   │   └── errors_{timestamp}.log.gz
│   └── errors.log
│
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py           # All dataclasses
│   │   └── schema.json           # JSON schema
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py               # BaseFetcher
│   │   ├── events.py
│   │   ├── commits.py
│   │   ├── pull_requests.py
│   │   ├── issues.py
│   │   ├── reviews.py
│   │   └── comments.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── metrics.py
│   │   └── filters.py
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   ├── markdown_report.py
│   │   └── validator.py
│   └── utils/
│       ├── __init__.py
│       ├── gh_client.py
│       ├── date_utils.py
│       ├── file_utils.py
│       ├── cache.py
│       ├── logger.py
│       ├── log_cleanup.py
│       └── report_cleanup.py
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── generate_report.py            # Entry point
├── config.yaml                   # Configuration
├── pytest.ini
├── requirements.txt
└── README.md
```

### 4.3 GitHub API Data Sources

#### 4.3.1 Events API (Primary)

```bash
gh api /users/{username}/events --paginate
```

| Event Type | Description | Data Extracted |
|------------|-------------|----------------|
| `PushEvent` | Git push | commits, repo, branch |
| `PullRequestEvent` | PR opened/closed/merged | PR details, state |
| `PullRequestReviewEvent` | Review submitted | review body, state |
| `PullRequestReviewCommentEvent` | Review comment | comment, file, line |
| `IssueCommentEvent` | Issue/PR comment | comment body |
| `IssuesEvent` | Issue opened/closed | issue details, labels |
| `CreateEvent` | Repo/branch/tag created | ref type, name |
| `DeleteEvent` | Branch/tag deleted | ref type, name |
| `ReleaseEvent` | Release published | release tag, body |

#### 4.3.2 Search APIs (Supplementary)

```bash
gh search commits --author={username} --committer-date={range}
gh search prs --author={username} --created={range}
gh search issues --author={username} --created={range}
```

#### 4.3.3 GraphQL API (Aggregated Stats)

```graphql
query {
  viewer {
    contributionsCollection(from: "...", to: "...") {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
```

---

## 5. JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GitHub Activity Report",
  "type": "object",
  "required": ["metadata", "summary", "activity"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["generated_at", "user", "period"],
      "properties": {
        "generated_at": { "type": "string", "format": "date-time" },
        "user": {
          "type": "object",
          "properties": {
            "login": { "type": "string" },
            "id": { "type": "integer" },
            "name": { "type": "string" }
          }
        },
        "period": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["monthly", "quarterly"] },
            "year": { "type": "integer" },
            "month": { "type": "integer", "minimum": 1, "maximum": 12 },
            "quarter": { "type": "integer", "minimum": 1, "maximum": 4 },
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" }
          }
        },
        "schema_version": { "type": "string" }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_commits": { "type": "integer" },
        "total_prs_opened": { "type": "integer" },
        "total_prs_merged": { "type": "integer" },
        "total_prs_reviewed": { "type": "integer" },
        "total_issues_opened": { "type": "integer" },
        "total_issues_closed": { "type": "integer" },
        "total_comments": { "type": "integer" },
        "repos_contributed_to": { "type": "integer" },
        "most_active_day": { "type": "string" },
        "most_active_repo": { "type": "string" }
      }
    },
    "activity": {
      "type": "object",
      "properties": {
        "commits": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sha": { "type": "string" },
              "message": { "type": "string" },
              "repository": { "type": "string" },
              "date": { "type": "string", "format": "date-time" },
              "additions": { "type": "integer" },
              "deletions": { "type": "integer" }
            }
          }
        },
        "pull_requests": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "number": { "type": "integer" },
              "title": { "type": "string" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "created_at": { "type": "string" },
              "merged_at": { "type": "string" },
              "closed_at": { "type": "string" },
              "commits_count": { "type": "integer" },
              "additions": { "type": "integer" },
              "deletions": { "type": "integer" }
            }
          }
        },
        "reviews": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pr_number": { "type": "integer" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "submitted_at": { "type": "string" },
              "body_length": { "type": "integer" }
            }
          }
        },
        "issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "number": { "type": "integer" },
              "title": { "type": "string" },
              "repository": { "type": "string" },
              "state": { "type": "string" },
              "created_at": { "type": "string" },
              "closed_at": { "type": "string" },
              "labels": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "comments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "repository": { "type": "string" },
              "issue_number": { "type": "integer" },
              "created_at": { "type": "string" },
              "body_length": { "type": "integer" }
            }
          }
        },
        "repositories": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "commits": { "type": "integer" },
              "prs": { "type": "integer" },
              "issues": { "type": "integer" },
              "reviews": { "type": "integer" }
            }
          }
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "pr_metrics": {
          "type": "object",
          "properties": {
            "avg_commits_per_pr": { "type": "number" },
            "avg_time_to_merge_hours": { "type": "number" },
            "avg_time_to_first_review_hours": { "type": "number" },
            "avg_review_iterations": { "type": "number" },
            "prs_merged_without_changes": { "type": "integer" },
            "prs_with_requested_changes": { "type": "integer" }
          }
        },
        "review_metrics": {
          "type": "object",
          "properties": {
            "avg_review_turnaround_hours": { "type": "number" },
            "reviews_with_comments": { "type": "integer" },
            "approvals": { "type": "integer" },
            "changes_requested": { "type": "integer" }
          }
        },
        "engagement_metrics": {
          "type": "object",
          "properties": {
            "avg_response_time_hours": { "type": "number" },
            "comment_to_code_ratio": { "type": "number" },
            "collaboration_score": { "type": "number" }
          }
        },
        "productivity_by_day": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "productivity_by_hour": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        }
      }
    }
  }
}
```

---

## 6. Testing Strategy

### 6.1 Test Structure

```
tests/
├── conftest.py                   # Shared fixtures
├── fixtures/
│   ├── api_responses/            # Mock GitHub API responses
│   │   ├── events.json
│   │   ├── commits.json
│   │   ├── pull_requests.json
│   │   └── reviews.json
│   └── expected_outputs/         # Expected report outputs
├── unit/
│   ├── test_config.py            # Config loading tests
│   ├── test_fetchers.py          # Fetcher unit tests
│   ├── test_processors.py        # Processor unit tests
│   ├── test_reporters.py         # Reporter unit tests
│   └── test_utils.py             # Utility function tests
├── integration/
│   ├── test_cli.py               # CLI integration tests
│   ├── test_report_generation.py # Full flow tests
│   └── test_cleanup.py           # Cleanup integration tests
└── e2e/
    └── test_live_api.py          # Live API tests (optional)
```

### 6.2 Test Configuration

```ini
# pytest.ini

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

### 6.3 Key Test Cases

| Test Category | Test Case | Description |
|---------------|-----------|-------------|
| CLI | `test_default_options` | No args → current month |
| CLI | `test_month_quarter_exclusive` | -m and -q error |
| CLI | `test_user_autodetect` | Uses gh logged-in user |
| Fetching | `test_adaptive_weekly` | Normal week uses week data |
| Fetching | `test_adaptive_daily` | High activity switches to daily |
| Cleanup | `test_version_cleanup` | Keeps only N versions |
| Cleanup | `test_error_rotation` | Rotates at size threshold |
| Reports | `test_json_schema_valid` | Output matches schema |
| Reports | `test_increment_filename` | Increments on regenerate |

---

## 7. Error Handling

### 7.1 Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| API Errors | Rate limit, timeout | Retry with backoff |
| Auth Errors | Invalid token | Exit with clear message |
| Config Errors | Invalid YAML | Exit with validation errors |
| File Errors | Permission denied | Log and skip or exit |
| Data Errors | Missing fields | Use defaults, log warning |

### 7.2 Retry Strategy

```python
def retry_with_backoff(func, max_retries=3, backoff_base=2.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_base ** attempt
            time.sleep(wait_time)
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Project structure setup
- [ ] Config loading (YAML + CLI + ENV)
- [ ] Logger implementation
- [ ] Basic CLI interface

### Phase 2: Data Fetching (Week 2)
- [ ] gh CLI wrapper
- [ ] Base fetcher with adaptive strategy
- [ ] Events, commits, PRs fetchers
- [ ] Response caching

### Phase 3: Processing (Week 3)
- [ ] Data aggregation
- [ ] Metrics calculation
- [ ] Date filtering
- [ ] Deduplication

### Phase 4: Reporting (Week 4)
- [ ] JSON report generator
- [ ] Schema validation
- [ ] Markdown report generator
- [ ] File naming with increment

### Phase 5: Cleanup & Polish (Week 5)
- [ ] Log cleanup implementation
- [ ] Report cleanup implementation
- [ ] Error handling refinement
- [ ] Documentation

### Phase 6: Testing (Week 6)
- [ ] Unit tests (80% coverage)
- [ ] Integration tests
- [ ] E2E tests (optional)
- [ ] CI/CD setup

---

## 9. Configuration File

The complete `config.yaml` combining all feature specifications:

```yaml
# =============================================================================
# GitHub Activity Report Generator - Configuration
# =============================================================================
# Priority: CLI > Environment Variables > config.yaml > Defaults
# =============================================================================

# -----------------------------------------------------------------------------
# Period Settings (Section 3.1)
# -----------------------------------------------------------------------------
period:
  default_type: monthly                   # monthly or quarterly (when no CLI flag)

# -----------------------------------------------------------------------------
# User Settings (Section 3.2)
# -----------------------------------------------------------------------------
user:
  username: null                          # null = auto-detect from gh CLI
  organizations: []                       # empty = all accessible orgs

# -----------------------------------------------------------------------------
# Repository Filters (Section 3.3)
# -----------------------------------------------------------------------------
repositories:
  include_private: true
  include_forks: false
  include: []                             # Whitelist (CLI: --include-repos)
  exclude: []                             # Blacklist (CLI: --exclude-repos)

# -----------------------------------------------------------------------------
# Fetching Strategy (Section 3.4)
# -----------------------------------------------------------------------------
fetching:
  high_activity_threshold: 100            # Switch to daily if >= 100 events/week
  request_delay: 1.0                      # Seconds between requests
  max_retries: 3
  backoff_base: 2.0
  timeout: 30

# -----------------------------------------------------------------------------
# Caching (Section 3.5)
# -----------------------------------------------------------------------------
cache:
  enabled: true
  directory: .cache
  ttl_hours: 24

# -----------------------------------------------------------------------------
# Output & Reports (Section 3.6)
# -----------------------------------------------------------------------------
output:
  directory: reports
  formats:
    - json
    - markdown
  include_links: true
  commit_message_format: truncated        # full, first_line, truncated

# -----------------------------------------------------------------------------
# Metrics (Section 3.7)
# -----------------------------------------------------------------------------
metrics:
  pr_metrics: true
  review_metrics: true
  engagement_metrics: true
  productivity_patterns: true
  reaction_breakdown: true

# -----------------------------------------------------------------------------
# Logging (Section 3.8)
# -----------------------------------------------------------------------------
logging:
  level: INFO                             # DEBUG, INFO, WARNING, ERROR, TRACE
  colorize: true
  show_timestamps: true
  progress_style: rich                    # rich, simple, none

  file:
    enabled: true
    directory: logs
    organize_by_date: true
    timestamp_format: "%Y-%m-%d_%H%M%S"
    format: jsonl                         # jsonl, text
    separate_errors: true
    error_file: errors.log
    performance_log: true

    # Log Cleanup (Section 3.9)
    cleanup:
      trigger: startup                    # startup, shutdown, both, manual
      retention_days: 30
      retention_days_performance: 14
      max_total_size_mb: 500
      max_file_size_mb: 50
      max_files: 100
      keep_minimum_days: 7
      strategy: oldest_first              # oldest_first, largest_first

      error_log:
        max_size_mb: 10                   # Rotate when exceeded
        max_files: 50
        max_age_days: 365
        compress_rotated: true

  include:
    timestamps: true
    module_name: true
    line_numbers: false
    stack_traces: false

  performance:
    log_api_calls: true
    log_timing: true
    log_memory: false
    slow_threshold_ms: 1000

# -----------------------------------------------------------------------------
# Report Cleanup (Section 3.10)
# -----------------------------------------------------------------------------
output_cleanup:
  enabled: true
  trigger: startup
  retention_years: 2
  keep_versions: 3
  max_total_size_mb: 1000
  max_file_size_mb: 100
  max_reports: 500
  keep_minimum_months: 6
  strategy: oldest_first

  archive:
    enabled: true
    directory: reports/archive
    compress: true
    archive_after_days: 365

# -----------------------------------------------------------------------------
# Advanced Settings
# -----------------------------------------------------------------------------
advanced:
  schema_version: "1.0"
  timezone: null                          # null = local timezone
  include_draft_prs: true
  separate_author_reviewer_stats: true
```

---

## Document Validation

To verify this document's internal consistency:

1. **Cross-Reference Check**: Ensure Master Reference table (Section 2.2) matches all feature specifications
2. **Config Validation**: Verify config.yaml (Section 9) includes all settings from Sections 3.1-3.10
3. **Dataclass Check**: Verify all dataclass defaults match specification defaults
4. **Checklist Review**: Complete all validation checklists in each feature section

---

*Document Version: 2.1*
*Last Updated: 2026-01-04*
*Pattern: Specification-Implementation*

---

## Changelog

### v2.1 (2026-01-04)
- Updated CLI options to match implementation:
  - Removed `-o/--orgs` (organizations is config-only)
  - Replaced `-v/--verbose` with `--log-level`
  - Replaced `--include-private`/`--include-forks` with `--include-repos`/`--exclude-repos`
  - Changed `-o` short form from orgs to output-dir
- Updated `commit_message_format` default from `"first_line"` to `"truncated"`
- Updated directory structure to show user grouping: `reports/{year}/{username}/`
- Added `repositories.include` whitelist alongside existing `exclude` blacklist
