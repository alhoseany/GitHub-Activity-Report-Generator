# GitHub Activity Report Generator - Implementation Guide

> **For AI Agents**: Step-by-step guide to implement the GitHub Activity Report Generator following the use case tasks.

---

## Overview

This document guides you through implementing the GitHub Activity Report Generator. Follow the use cases in order - each builds on the previous.

### Document References

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `tasks-by-usecase.md` | Task details & acceptance criteria | Primary reference for each task |
| `plan-v2.md` | Full specifications & code samples | When you need implementation details |
| `tasks.md` | Technical task breakdown | Cross-reference for TASK-X.Y IDs |

### Implementation Rules

1. **One use case at a time** - Complete and verify before moving on
2. **Check acceptance criteria** - Every task has checkboxes to verify
3. **Use code markers** - Tag all code with task and plan references
4. **Test as you go** - Verify each component works before integration
5. **No over-engineering** - Implement exactly what's specified

---

## Code Marker Format

Every file and significant function must include traceability markers:

```python
# =============================================================================
# FILE: src/config/settings.py
# TASKS: UC-4.1, UC-5.1, UC-7.1
# PLAN: Section 3.2, 3.3, 3.7
# =============================================================================

@dataclass
class UserConfig:  # UC-4.1 | PLAN-3.2
    """User configuration settings."""
    username: str | None = None
    organizations: list[str] = field(default_factory=list)
```

---

## Phase 1: Core Setup

### UC-1.1: Create Project Structure

**Reference:** `tasks-by-usecase.md` → UC-1.1

**Steps:**

1. Create the directory structure:
```bash
mkdir -p .scripts/github-activity/{src/{config,fetchers,processors,reporters,utils},tests/{fixtures/{api_responses,expected_outputs},unit,integration,e2e},reports,logs/errors,.cache}
```

2. Create `__init__.py` files in all Python packages:
```bash
touch .scripts/github-activity/src/__init__.py
touch .scripts/github-activity/src/config/__init__.py
touch .scripts/github-activity/src/fetchers/__init__.py
touch .scripts/github-activity/src/processors/__init__.py
touch .scripts/github-activity/src/reporters/__init__.py
touch .scripts/github-activity/src/utils/__init__.py
touch .scripts/github-activity/tests/__init__.py
```

3. Create `.gitkeep` in empty directories:
```bash
touch .scripts/github-activity/reports/.gitkeep
touch .scripts/github-activity/logs/.gitkeep
touch .scripts/github-activity/logs/errors/.gitkeep
touch .scripts/github-activity/.cache/.gitkeep
```

**Verify:**
- [ ] All directories exist
- [ ] All `__init__.py` files present
- [ ] `.gitkeep` in empty directories

---

### UC-1.2: Install Dependencies

**Reference:** `tasks-by-usecase.md` → UC-1.2

**Steps:**

1. Create `requirements.txt`:
```
# Core dependencies
click>=8.0.0
pyyaml>=6.0
jsonschema>=4.0.0
python-dateutil>=2.8.0
rich>=13.0.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0

# Code quality
black>=23.0.0
ruff>=0.1.0
mypy>=1.0.0
```

2. Create `pytest.ini`:
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

**Verify:**
```bash
cd .scripts/github-activity
pip install -r requirements.txt
pytest --collect-only  # Should not error
```

- [ ] `pip install` succeeds
- [ ] `pytest` runs without import errors

---

## Phase 2: Basic Functionality

### UC-2.1: Create CLI Entry Point

**Reference:** `tasks-by-usecase.md` → UC-2.1, `plan-v2.md` → Section 3.1

**Steps:**

1. Create `generate_report.py` (entry point):

```python
#!/usr/bin/env python3
# =============================================================================
# FILE: generate_report.py
# TASKS: UC-2.1
# PLAN: Section 3.1
# =============================================================================

import click
import subprocess
from datetime import datetime


def get_current_quarter() -> int:  # UC-2.1 | PLAN-3.1
    """Return current quarter (1-4) based on current month."""
    return (datetime.now().month - 1) // 3 + 1


def get_logged_in_user() -> str:  # UC-2.1 | PLAN-3.1
    """Get currently logged-in GitHub user from gh CLI."""
    result = subprocess.run(
        ["gh", "api", "/user", "--jq", ".login"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise click.ClickException("Failed to get GitHub user. Is gh CLI authenticated?")
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

    # Validate mutual exclusivity  # UC-2.1 | PLAN-3.1
    if month is not None and quarter is not None:
        raise click.UsageError("Cannot use --month and --quarter together")

    # Apply smart defaults  # UC-2.1 | PLAN-3.1
    if user is None:
        user = get_logged_in_user()

    if month is None and quarter is None:
        month = datetime.now().month  # Default to current month

    # Determine period type
    if quarter is not None:
        period_type = "quarterly"
        period_value = quarter
    else:
        period_type = "monthly"
        period_value = month

    click.echo(f"Generating {period_type} report for {user}")
    click.echo(f"Period: {period_type} {period_value}, Year: {year}")

    # TODO: Implement full pipeline in UC-2.5


if __name__ == "__main__":
    main()
```

2. Make executable:
```bash
chmod +x generate_report.py
```

**Verify:**
```bash
./generate_report.py --help
./generate_report.py  # Should show current month for logged-in user
./generate_report.py -m 6 -q 2  # Should error (mutual exclusivity)
```

- [ ] `--help` shows all 10 options
- [ ] Running with no args uses current month
- [ ] User auto-detected from gh CLI
- [ ] `-m` and `-q` together produces error

---

### UC-2.2: Fetch GitHub Data

**Reference:** `tasks-by-usecase.md` → UC-2.2, `plan-v2.md` → Sections 3.4, 4.3

**Steps:**

1. Create `src/utils/gh_client.py`:

```python
# =============================================================================
# FILE: src/utils/gh_client.py
# TASKS: UC-2.2
# PLAN: Section 4.3
# =============================================================================

import subprocess
import json
import time
from typing import Any


class GitHubClient:  # UC-2.2 | PLAN-4.3
    """Wrapper for gh CLI commands."""

    def __init__(self, request_delay: float = 1.0):
        self.request_delay = request_delay

    def api(self, endpoint: str, **kwargs) -> dict | list:
        """Call GitHub API via gh CLI."""
        cmd = ["gh", "api", endpoint]

        if kwargs.get("paginate"):
            cmd.append("--paginate")

        if "jq" in kwargs:
            cmd.extend(["--jq", kwargs["jq"]])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"GitHub API error: {result.stderr}")

        time.sleep(self.request_delay)
        return json.loads(result.stdout) if result.stdout.strip() else []

    def search(self, search_type: str, query: str, **kwargs) -> list:
        """Execute gh search command."""
        cmd = ["gh", "search", search_type, query, "--json", "url,title,state,createdAt"]

        if "limit" in kwargs:
            cmd.extend(["--limit", str(kwargs["limit"])])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"GitHub search error: {result.stderr}")

        time.sleep(self.request_delay)
        return json.loads(result.stdout) if result.stdout.strip() else []
```

2. Create `src/fetchers/base.py` (from plan-v2.md Section 3.4.3):

```python
# =============================================================================
# FILE: src/fetchers/base.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================

from datetime import date, timedelta
from typing import Iterator
import time


class BaseFetcher:  # UC-2.2 | PLAN-3.4
    """Base class for all data fetchers with adaptive strategy."""

    def __init__(self, gh_client, config, logger=None):
        self.gh = gh_client
        self.config = config
        self.logger = logger
        self.high_activity_threshold = getattr(config, 'high_activity_threshold', 100)
        self.request_delay = getattr(config, 'request_delay', 1.0)

    def fetch_period(self, start_date: date, end_date: date) -> list[dict]:
        """Fetch data using adaptive week/day granularity."""
        all_events = []

        for week_start, week_end in self._iter_weeks(start_date, end_date):
            week_events = self._fetch_range(week_start, week_end)

            if len(week_events) >= self.high_activity_threshold:
                if self.logger:
                    self.logger.info(
                        f"High activity ({len(week_events)} events), switching to daily"
                    )
                week_events = self._fetch_week_by_days(week_start, week_end)

            all_events.extend(week_events)

        return self._deduplicate(all_events)

    def _iter_weeks(self, start: date, end: date) -> Iterator[tuple[date, date]]:
        """Iterate through weeks."""
        current = start
        while current <= end:
            week_end = min(current + timedelta(days=6), end)
            yield (current, week_end)
            current = week_end + timedelta(days=1)

    def _fetch_week_by_days(self, week_start: date, week_end: date) -> list[dict]:
        """Fetch high-activity week day by day."""
        daily_events = []
        current = week_start

        while current <= week_end:
            day_events = self._fetch_range(current, current)
            daily_events.extend(day_events)
            current += timedelta(days=1)

        return daily_events

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch data for date range. Override in subclasses."""
        raise NotImplementedError

    def _deduplicate(self, events: list[dict]) -> list[dict]:
        """Remove duplicates based on unique ID."""
        seen = set()
        unique = []
        for event in events:
            event_id = self._get_event_id(event)
            if event_id and event_id not in seen:
                seen.add(event_id)
                unique.append(event)
        return unique

    def _get_event_id(self, event: dict) -> str:
        """Get unique ID. Override in subclasses."""
        return event.get("id") or event.get("sha") or event.get("url")
```

3. Create fetchers for each data type:

**`src/fetchers/events.py`:**
```python
# =============================================================================
# FILE: src/fetchers/events.py
# TASKS: UC-2.2
# PLAN: Section 4.3.1
# =============================================================================

from .base import BaseFetcher
from datetime import date


class EventsFetcher(BaseFetcher):  # UC-2.2 | PLAN-4.3.1
    """Fetch user events from GitHub Events API."""

    def __init__(self, gh_client, config, username: str, logger=None):
        super().__init__(gh_client, config, logger)
        self.username = username

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch events for date range."""
        events = self.gh.api(
            f"/users/{self.username}/events",
            paginate=True
        )

        # Filter by date range
        filtered = []
        for event in events:
            event_date = event.get("created_at", "")[:10]
            if start.isoformat() <= event_date <= end.isoformat():
                filtered.append(event)

        return filtered

    def _get_event_id(self, event: dict) -> str:
        return event.get("id")
```

**`src/fetchers/commits.py`:**
```python
# =============================================================================
# FILE: src/fetchers/commits.py
# TASKS: UC-2.2
# PLAN: Section 4.3.2
# =============================================================================

from .base import BaseFetcher
from datetime import date


class CommitsFetcher(BaseFetcher):  # UC-2.2 | PLAN-4.3.2
    """Fetch commits using gh search."""

    def __init__(self, gh_client, config, username: str, logger=None):
        super().__init__(gh_client, config, logger)
        self.username = username

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch commits for date range."""
        query = f"author:{self.username} committer-date:{start}..{end}"
        return self.gh.search("commits", query, limit=100)

    def _get_event_id(self, event: dict) -> str:
        return event.get("sha") or event.get("url")
```

**`src/fetchers/pull_requests.py`:**
```python
# =============================================================================
# FILE: src/fetchers/pull_requests.py
# TASKS: UC-2.2
# PLAN: Section 4.3.2
# =============================================================================

from .base import BaseFetcher
from datetime import date


class PullRequestsFetcher(BaseFetcher):  # UC-2.2 | PLAN-4.3.2
    """Fetch pull requests using gh search."""

    def __init__(self, gh_client, config, username: str, logger=None):
        super().__init__(gh_client, config, logger)
        self.username = username

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch PRs for date range."""
        query = f"author:{self.username} created:{start}..{end}"
        return self.gh.search("prs", query, limit=100)

    def _get_event_id(self, event: dict) -> str:
        return event.get("url")
```

**`src/fetchers/issues.py`:**
```python
# =============================================================================
# FILE: src/fetchers/issues.py
# TASKS: UC-2.2
# PLAN: Section 4.3.2
# =============================================================================

from .base import BaseFetcher
from datetime import date


class IssuesFetcher(BaseFetcher):  # UC-2.2 | PLAN-4.3.2
    """Fetch issues using gh search."""

    def __init__(self, gh_client, config, username: str, logger=None):
        super().__init__(gh_client, config, logger)
        self.username = username

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Fetch issues for date range."""
        query = f"author:{self.username} created:{start}..{end}"
        return self.gh.search("issues", query, limit=100)

    def _get_event_id(self, event: dict) -> str:
        return event.get("url")
```

**`src/fetchers/reviews.py`:**
```python
# =============================================================================
# FILE: src/fetchers/reviews.py
# TASKS: UC-2.2
# PLAN: Section 4.3.2
# =============================================================================

from .base import BaseFetcher
from datetime import date


class ReviewsFetcher(BaseFetcher):  # UC-2.2 | PLAN-4.3.2
    """Fetch PR reviews."""

    def __init__(self, gh_client, config, username: str, logger=None):
        super().__init__(gh_client, config, logger)
        self.username = username

    def fetch_for_pr(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch reviews for a specific PR."""
        reviews = self.gh.api(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        )
        return [r for r in reviews if r.get("user", {}).get("login") == self.username]

    def _fetch_range(self, start: date, end: date) -> list[dict]:
        """Reviews are fetched per-PR, not by date range."""
        return []

    def _get_event_id(self, event: dict) -> str:
        return str(event.get("id"))
```

4. Create `src/fetchers/__init__.py`:
```python
from .base import BaseFetcher
from .events import EventsFetcher
from .commits import CommitsFetcher
from .pull_requests import PullRequestsFetcher
from .issues import IssuesFetcher
from .reviews import ReviewsFetcher

__all__ = [
    "BaseFetcher",
    "EventsFetcher",
    "CommitsFetcher",
    "PullRequestsFetcher",
    "IssuesFetcher",
    "ReviewsFetcher",
]
```

**Verify:**
```python
# Test in Python REPL
from src.utils.gh_client import GitHubClient
from src.fetchers import EventsFetcher

gh = GitHubClient()
user = "your-username"  # Replace with actual
# fetcher = EventsFetcher(gh, None, user)
# events = fetcher.fetch_period(date(2024, 12, 1), date(2024, 12, 31))
```

- [ ] All 5 fetcher classes created
- [ ] BaseFetcher has adaptive strategy (week → day)
- [ ] Rate limiting (1 second delay) implemented
- [ ] Deduplication works

---

### UC-2.3: Process and Aggregate Data

**Reference:** `tasks-by-usecase.md` → UC-2.3, `plan-v2.md` → Section 4.1

**Steps:**

1. Create `src/processors/aggregator.py`:

```python
# =============================================================================
# FILE: src/processors/aggregator.py
# TASKS: UC-2.3
# PLAN: Section 4.1
# =============================================================================

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class AggregatedData:  # UC-2.3 | PLAN-4.1
    """Container for aggregated activity data."""
    commits: list[dict] = field(default_factory=list)
    pull_requests: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)

    @property
    def summary(self) -> dict:
        """Generate summary statistics."""
        return {
            "total_commits": len(self.commits),
            "total_prs_opened": len(self.pull_requests),
            "total_prs_merged": sum(1 for pr in self.pull_requests if pr.get("merged_at")),
            "total_prs_reviewed": len(self.reviews),
            "total_issues_opened": len(self.issues),
            "total_issues_closed": sum(1 for i in self.issues if i.get("closed_at")),
            "total_comments": len(self.comments),
        }


class DataAggregator:  # UC-2.3 | PLAN-4.1
    """Aggregate and process fetched data."""

    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date

    def aggregate(
        self,
        events: list[dict],
        commits: list[dict],
        prs: list[dict],
        issues: list[dict],
        reviews: list[dict]
    ) -> AggregatedData:
        """Aggregate all data sources."""

        # Extract comments from events
        comments = [
            e for e in events
            if e.get("type") in ("IssueCommentEvent", "PullRequestReviewCommentEvent")
        ]

        return AggregatedData(
            commits=self._filter_by_date(commits),
            pull_requests=self._filter_by_date(prs),
            issues=self._filter_by_date(issues),
            reviews=reviews,
            comments=comments,
        )

    def _filter_by_date(self, items: list[dict]) -> list[dict]:
        """Filter items by date range."""
        filtered = []
        for item in items:
            item_date = self._extract_date(item)
            if item_date and self.start_date <= item_date <= self.end_date:
                filtered.append(item)
        return filtered

    def _extract_date(self, item: dict) -> date | None:
        """Extract date from item."""
        for field in ("created_at", "date", "committed_date"):
            if field in item:
                try:
                    return date.fromisoformat(item[field][:10])
                except (ValueError, TypeError):
                    pass
        return None
```

2. Create `src/processors/__init__.py`:
```python
from .aggregator import AggregatedData, DataAggregator

__all__ = ["AggregatedData", "DataAggregator"]
```

**Verify:**
- [ ] `AggregatedData` holds all 5 data types
- [ ] Date filtering works
- [ ] Summary statistics calculated correctly

---

### UC-2.4: Generate Reports

**Reference:** `tasks-by-usecase.md` → UC-2.4, `plan-v2.md` → Sections 3.6, 5

**Steps:**

1. Create `src/config/schema.json` (copy from plan-v2.md Section 5)

2. Create `src/reporters/json_report.py`:

```python
# =============================================================================
# FILE: src/reporters/json_report.py
# TASKS: UC-2.4
# PLAN: Section 3.6, 5
# =============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonReporter:  # UC-2.4 | PLAN-3.6
    """Generate JSON reports."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)

    def generate(
        self,
        data: Any,  # AggregatedData
        user: str,
        year: int,
        period_type: str,
        period_value: int,
        metrics: dict | None = None
    ) -> dict:
        """Generate JSON report structure."""

        start_date, end_date = self._get_period_dates(year, period_type, period_value)

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "user": {"login": user},
                "period": {
                    "type": period_type,
                    "year": year,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "schema_version": "1.0",
            },
            "summary": data.summary,
            "activity": {
                "commits": data.commits,
                "pull_requests": data.pull_requests,
                "issues": data.issues,
                "reviews": data.reviews,
                "comments": data.comments,
            },
        }

        if period_type == "monthly":
            report["metadata"]["period"]["month"] = period_value
        else:
            report["metadata"]["period"]["quarter"] = period_value

        if metrics:
            report["metrics"] = metrics

        return report

    def _get_period_dates(self, year: int, period_type: str, value: int) -> tuple[str, str]:
        """Get start and end dates for period."""
        from calendar import monthrange

        if period_type == "monthly":
            _, last_day = monthrange(year, value)
            return (f"{year}-{value:02d}-01", f"{year}-{value:02d}-{last_day:02d}")
        else:
            quarters = {
                1: (f"{year}-01-01", f"{year}-03-31"),
                2: (f"{year}-04-01", f"{year}-06-30"),
                3: (f"{year}-07-01", f"{year}-09-30"),
                4: (f"{year}-10-01", f"{year}-12-31"),
            }
            return quarters[value]
```

3. Create `src/reporters/markdown_report.py`:

```python
# =============================================================================
# FILE: src/reporters/markdown_report.py
# TASKS: UC-2.4
# PLAN: Section 3.6
# =============================================================================

from datetime import datetime
from typing import Any


class MarkdownReporter:  # UC-2.4 | PLAN-3.6
    """Generate Markdown reports."""

    def __init__(self, include_links: bool = True):
        self.include_links = include_links

    def generate(self, report_data: dict) -> str:
        """Generate Markdown from JSON report data."""
        metadata = report_data["metadata"]
        summary = report_data["summary"]
        activity = report_data["activity"]

        period = metadata["period"]
        if "month" in period:
            period_str = f"{period['year']}-{period['month']:02d}"
        else:
            period_str = f"{period['year']}-Q{period['quarter']}"

        lines = [
            f"# GitHub Activity Report: {period_str}",
            "",
            f"**User:** {metadata['user']['login']}",
            f"**Period:** {period['start_date']} to {period['end_date']}",
            f"**Generated:** {metadata['generated_at']}",
            "",
            "## Summary",
            "",
            f"- **Commits:** {summary['total_commits']}",
            f"- **PRs Opened:** {summary['total_prs_opened']}",
            f"- **PRs Merged:** {summary['total_prs_merged']}",
            f"- **PRs Reviewed:** {summary['total_prs_reviewed']}",
            f"- **Issues Opened:** {summary['total_issues_opened']}",
            f"- **Issues Closed:** {summary['total_issues_closed']}",
            f"- **Comments:** {summary['total_comments']}",
            "",
        ]

        # Add activity sections
        if activity.get("commits"):
            lines.extend(self._format_commits(activity["commits"]))

        if activity.get("pull_requests"):
            lines.extend(self._format_prs(activity["pull_requests"]))

        if activity.get("issues"):
            lines.extend(self._format_issues(activity["issues"]))

        return "\n".join(lines)

    def _format_commits(self, commits: list[dict]) -> list[str]:
        """Format commits section."""
        lines = ["## Commits", ""]
        for commit in commits[:50]:  # Limit for readability
            msg = commit.get("message", "").split("\n")[0][:80]
            lines.append(f"- {msg}")
        if len(commits) > 50:
            lines.append(f"- ... and {len(commits) - 50} more")
        lines.append("")
        return lines

    def _format_prs(self, prs: list[dict]) -> list[str]:
        """Format PRs section."""
        lines = ["## Pull Requests", ""]
        for pr in prs:
            title = pr.get("title", "Untitled")
            state = pr.get("state", "unknown")
            lines.append(f"- [{state}] {title}")
        lines.append("")
        return lines

    def _format_issues(self, issues: list[dict]) -> list[str]:
        """Format issues section."""
        lines = ["## Issues", ""]
        for issue in issues:
            title = issue.get("title", "Untitled")
            state = issue.get("state", "unknown")
            lines.append(f"- [{state}] {title}")
        lines.append("")
        return lines
```

4. Create `src/utils/file_utils.py`:

```python
# =============================================================================
# FILE: src/utils/file_utils.py
# TASKS: UC-2.4
# PLAN: Section 3.6
# =============================================================================

import json
from pathlib import Path
from typing import Literal


def get_next_filename(
    base_dir: Path,
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int,
    extension: str = "md"
) -> Path:  # UC-2.4 | PLAN-3.6
    """Get next available filename with increment."""
    year_dir = base_dir / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    if period_type == "monthly":
        prefix = f"{year}-{period_value:02d}-github-activity"
    else:
        prefix = f"{year}-Q{period_value}-github-activity"

    pattern = f"{prefix}-*.{extension}"
    existing = sorted(year_dir.glob(pattern))

    if not existing:
        return year_dir / f"{prefix}-1.{extension}"

    last_file = existing[-1]
    last_num = int(last_file.stem.split("-")[-1])
    return year_dir / f"{prefix}-{last_num + 1}.{extension}"


def write_report(file_path: Path, content: str | dict):  # UC-2.4 | PLAN-3.6
    """Write report to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, dict):
        with open(file_path, "w") as f:
            json.dump(content, f, indent=2, default=str)
    else:
        with open(file_path, "w") as f:
            f.write(content)
```

5. Create `src/reporters/__init__.py`:
```python
from .json_report import JsonReporter
from .markdown_report import MarkdownReporter

__all__ = ["JsonReporter", "MarkdownReporter"]
```

**Verify:**
- [ ] JSON report matches schema structure
- [ ] Markdown is human-readable
- [ ] Filenames increment correctly (test by running twice)

---

### UC-2.5: Orchestrate Full Pipeline

**Reference:** `tasks-by-usecase.md` → UC-2.5, `plan-v2.md` → Section 4.1

**Steps:**

1. Create `src/orchestrator.py`:

```python
# =============================================================================
# FILE: src/orchestrator.py
# TASKS: UC-2.5
# PLAN: Section 4.1
# =============================================================================

from datetime import date
from pathlib import Path

from .utils.gh_client import GitHubClient
from .utils.file_utils import get_next_filename, write_report
from .fetchers import (
    EventsFetcher, CommitsFetcher, PullRequestsFetcher,
    IssuesFetcher, ReviewsFetcher
)
from .processors import DataAggregator
from .reporters import JsonReporter, MarkdownReporter


class ReportOrchestrator:  # UC-2.5 | PLAN-4.1
    """Orchestrate the full report generation pipeline."""

    def __init__(
        self,
        user: str,
        year: int,
        period_type: str,
        period_value: int,
        output_dir: str = "reports",
        output_format: str = "both",
        cache_enabled: bool = True,
        verbose: int = 0,
        config: dict | None = None
    ):
        self.user = user
        self.year = year
        self.period_type = period_type
        self.period_value = period_value
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        self.cache_enabled = cache_enabled
        self.verbose = verbose
        self.config = config or {}

        # Initialize components
        self.gh = GitHubClient()
        self.start_date, self.end_date = self._get_period_dates()
        self.logger = None  # Initialized in run()

    def run(self) -> list[Path]:
        """
        Execute full pipeline and return generated file paths.

        Pipeline steps (per UC-2.5 / PLAN-4.1):
        1. Load config (done in __init__)
        2. Initialize logger
        3. Run cleanup (if trigger=startup)
        4. Fetch data
        5. Aggregate data
        6. Calculate metrics
        7. Generate reports
        8. Run cleanup (if trigger=shutdown)
        """
        generated_files = []

        # Step 2: Initialize logger
        # TODO: self.logger = StructuredLogger("github-activity", self.config.get("logging", {}))
        if self.verbose:
            print(f"Starting report generation for {self.user}")

        # Step 3: Run cleanup if trigger=startup
        cleanup_trigger = self.config.get("logging", {}).get("file", {}).get("cleanup", {}).get("trigger", "startup")
        if cleanup_trigger in ("startup", "both"):
            self._run_cleanup()

        # Step 4: Fetch data
        if self.verbose:
            print(f"Fetching data for {self.user}...")

        events = EventsFetcher(self.gh, self, self.user).fetch_period(
            self.start_date, self.end_date
        )
        commits = CommitsFetcher(self.gh, self, self.user).fetch_period(
            self.start_date, self.end_date
        )
        prs = PullRequestsFetcher(self.gh, self, self.user).fetch_period(
            self.start_date, self.end_date
        )
        issues = IssuesFetcher(self.gh, self, self.user).fetch_period(
            self.start_date, self.end_date
        )

        # Step 5: Aggregate data
        if self.verbose:
            print("Aggregating data...")

        aggregator = DataAggregator(self.start_date, self.end_date)
        data = aggregator.aggregate(events, commits, prs, issues, [])

        # Step 6: Calculate metrics
        metrics = None
        metrics_config = self.config.get("metrics", {})
        if any(metrics_config.get(k, True) for k in [
            "pr_metrics", "review_metrics", "engagement_metrics",
            "productivity_patterns", "reaction_breakdown"
        ]):
            if self.verbose:
                print("Calculating metrics...")
            # TODO: metrics = MetricsCalculator(metrics_config).calculate_all(data)

        # Step 7: Generate reports
        if self.verbose:
            print("Generating reports...")

        json_reporter = JsonReporter(str(self.output_dir))
        report_data = json_reporter.generate(
            data, self.user, self.year,
            self.period_type, self.period_value,
            metrics=metrics
        )

        # Write JSON
        if self.output_format in ("json", "both"):
            json_path = get_next_filename(
                self.output_dir, self.year,
                self.period_type, self.period_value, "json"
            )
            write_report(json_path, report_data)
            generated_files.append(json_path)
            if self.verbose:
                print(f"Created: {json_path}")

        # Write Markdown
        if self.output_format in ("markdown", "both"):
            md_reporter = MarkdownReporter()
            md_content = md_reporter.generate(report_data)
            md_path = get_next_filename(
                self.output_dir, self.year,
                self.period_type, self.period_value, "md"
            )
            write_report(md_path, md_content)
            generated_files.append(md_path)
            if self.verbose:
                print(f"Created: {md_path}")

        # Step 8: Run cleanup if trigger=shutdown
        if cleanup_trigger in ("shutdown", "both"):
            self._run_cleanup()

        return generated_files

    def _run_cleanup(self):
        """Run log and report cleanup based on config."""
        if self.verbose:
            print("Running cleanup...")
        # TODO: Implement cleanup calls
        # LogCleaner(Path("logs"), self.config.get("logging", {}).get("file", {}).get("cleanup", {})).cleanup()
        # ReportCleaner(self.output_dir, self.config.get("output_cleanup", {})).cleanup()

    def _get_period_dates(self) -> tuple[date, date]:
        """Get start and end dates for the period."""
        from calendar import monthrange

        if self.period_type == "monthly":
            _, last_day = monthrange(self.year, self.period_value)
            return (
                date(self.year, self.period_value, 1),
                date(self.year, self.period_value, last_day)
            )
        else:
            quarters = {
                1: (date(self.year, 1, 1), date(self.year, 3, 31)),
                2: (date(self.year, 4, 1), date(self.year, 6, 30)),
                3: (date(self.year, 7, 1), date(self.year, 9, 30)),
                4: (date(self.year, 10, 1), date(self.year, 12, 31)),
            }
            return quarters[self.period_value]
```

2. Update `generate_report.py` to use orchestrator:

```python
# Add to generate_report.py main() function, replacing the TODO:

from src.orchestrator import ReportOrchestrator
from src.config.loader import load_config

# ... after determining period_type and period_value ...

# Load configuration (CLI overrides will be applied in orchestrator)
config = load_config()

orchestrator = ReportOrchestrator(
    user=user,
    year=year,
    period_type=period_type,
    period_value=period_value,
    output_dir=output_dir,
    output_format=output_format,
    cache_enabled=not no_cache,
    verbose=verbose,
    config=config
)

try:
    files = orchestrator.run()
    click.echo(f"\nGenerated {len(files)} report(s):")
    for f in files:
        click.echo(f"  - {f}")
except Exception as e:
    raise click.ClickException(str(e))
```

**Verify:**
```bash
./generate_report.py -v
# Should create reports/YYYY/YYYY-MM-github-activity-1.json and .md
```

- [ ] Full pipeline executes
- [ ] Both JSON and Markdown files created
- [ ] Progress shown when verbose
- [ ] Errors handled gracefully

---

## Phase 3: Period & Filtering

### UC-3.1: Support Period Selection

Already implemented in UC-2.1. Verify:

- [ ] `-m 6` generates June report
- [ ] `-q 2` generates Q2 report
- [ ] `-m 6 -y 2023` generates June 2023
- [ ] `-m` and `-q` together produces error

---

### UC-4.1: Configure User Settings

**Reference:** `tasks-by-usecase.md` → UC-4.1, `plan-v2.md` → Section 3.2

**Steps:**

1. Create `src/config/settings.py`:

```python
# =============================================================================
# FILE: src/config/settings.py
# TASKS: UC-4.1, UC-5.1, UC-6.1, UC-7.1, UC-8.1, UC-9.1, UC-10.1, UC-11.1
# PLAN: Sections 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
# =============================================================================

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class UserConfig:  # UC-4.1 | PLAN-3.2
    """User configuration settings."""
    username: str | None = None
    organizations: list[str] = field(default_factory=list)


@dataclass
class RepositoryConfig:  # UC-5.1 | PLAN-3.3
    """Repository filter configuration."""
    include_private: bool = True
    include_forks: bool = False
    exclude: list[str] = field(default_factory=list)


@dataclass
class FetchingConfig:  # UC-2.2 | PLAN-3.4
    """Fetching strategy configuration."""
    high_activity_threshold: int = 100
    request_delay: float = 1.0
    max_retries: int = 3
    backoff_base: float = 2.0
    timeout: int = 30


@dataclass
class CacheConfig:  # UC-8.1 | PLAN-3.5
    """Caching configuration."""
    enabled: bool = True
    directory: str = ".cache"
    ttl_hours: int = 24


@dataclass
class OutputConfig:  # UC-6.1 | PLAN-3.6
    """Output configuration."""
    directory: str = "reports"
    formats: list[str] = field(default_factory=lambda: ["json", "markdown"])
    include_links: bool = True
    commit_message_format: Literal["full", "first_line", "truncated"] = "truncated"


@dataclass
class MetricsConfig:  # UC-7.1 | PLAN-3.7
    """Metrics calculation configuration."""
    pr_metrics: bool = True
    review_metrics: bool = True
    engagement_metrics: bool = True
    productivity_patterns: bool = True
    reaction_breakdown: bool = True


# Continue with LoggingConfig, LogCleanupConfig, ReportCleanupConfig...
# (See plan-v2.md Sections 3.8, 3.9, 3.10 for full implementations)
```

2. Create `src/config/loader.py`:

```python
# =============================================================================
# FILE: src/config/loader.py
# TASKS: UC-4.1
# PLAN: Section 2.1
# =============================================================================

import os
import yaml
from pathlib import Path
from .settings import *


def load_config(config_path: str = "config.yaml") -> dict:  # UC-4.1 | PLAN-2.1
    """
    Load configuration with priority:
    CLI > Environment Variables > config.yaml > Defaults
    """
    config = {}

    # Load from YAML if exists
    if Path(config_path).exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Apply environment variables
    env_mappings = {
        "GITHUB_ACTIVITY_USER": ("user", "username"),
        "GITHUB_ACTIVITY_OUTPUT_DIR": ("output", "directory"),
        "GITHUB_ACTIVITY_LOG_LEVEL": ("logging", "level"),
        "GITHUB_ACTIVITY_LOG_DIR": ("logging", "file", "directory"),
        "GITHUB_ACTIVITY_CACHE_DIR": ("cache", "directory"),
        "GITHUB_ACTIVITY_HIGH_THRESHOLD": ("fetching", "high_activity_threshold"),
    }

    for env_var, path in env_mappings.items():
        value = os.environ.get(env_var)
        if value:
            _set_nested(config, path, value)

    return config


def _set_nested(d: dict, path: tuple, value):
    """Set a nested dictionary value."""
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value
```

**Verify:**
```bash
GITHUB_ACTIVITY_USER=octocat ./generate_report.py
# Should use "octocat" as user
```

- [ ] Environment variable override works
- [ ] config.yaml loading works
- [ ] CLI overrides all

---

### UC-5.1: Configure Repository Filters

Already defined in `settings.py`. Update fetchers to use `RepositoryConfig.should_include()`.

CLI options:
- `--include-repos`: Whitelist specific repos (comma-separated)
- `--exclude-repos`: Blacklist specific repos (comma-separated)

Config-only settings:
- `repositories.include_private`: Include private repos (default: true)
- `repositories.include_forks`: Include forks (default: false)

- [ ] Private repos included by default
- [ ] Forks excluded by default
- [ ] `--include-repos` filters to whitelist
- [ ] `--exclude-repos` filters to blacklist

---

## Phase 4: Customization

### UC-6.1, UC-7.1, UC-8.1

These are configuration-based. The dataclasses are defined in `settings.py`. Wire them through the orchestrator.

---

## Phase 5: Operations

### UC-9.1: Configure Logging

**Reference:** `tasks-by-usecase.md` → UC-9.1, `plan-v2.md` → Section 3.8

Create `src/utils/logger.py` following plan-v2.md Section 3.8.3.

---

### UC-10.1: Configure Log Cleanup

**Reference:** `tasks-by-usecase.md` → UC-10.1, `plan-v2.md` → Section 3.9

Create `src/utils/log_cleanup.py` following plan-v2.md Section 3.9.3.

---

### UC-11.1: Configure Report Cleanup

**Reference:** `tasks-by-usecase.md` → UC-11.1, `plan-v2.md` → Section 3.10

Create `src/utils/report_cleanup.py` following plan-v2.md Section 3.10.3.

---

## Phase 6: Quality

### UC-12.1: Implement Schema Validation

**Reference:** `tasks-by-usecase.md` → UC-12.1, `plan-v2.md` → Section 5

Create `src/reporters/validator.py`:

```python
# =============================================================================
# FILE: src/reporters/validator.py
# TASKS: UC-12.1
# PLAN: Section 5
# =============================================================================

import json
from pathlib import Path
from jsonschema import validate, ValidationError


def validate_report(report_data: dict) -> tuple[bool, list[str]]:  # UC-12.1 | PLAN-5
    """Validate report against JSON schema."""
    schema_path = Path(__file__).parent.parent / "config" / "schema.json"

    with open(schema_path) as f:
        schema = json.load(f)

    errors = []
    try:
        validate(instance=report_data, schema=schema)
        return True, []
    except ValidationError as e:
        errors.append(str(e.message))
        return False, errors
```

---

### UC-13.1 & UC-13.2: Run Tests

Create test files in `tests/unit/` and `tests/integration/` following plan-v2.md Section 6.

---

## Verification Checklist

After completing all phases, verify:

### Phase 1
- [ ] Directory structure correct
- [ ] Dependencies install cleanly
- [ ] `pytest --collect-only` works

### Phase 2
- [ ] `./generate_report.py --help` shows all options
- [ ] Basic report generates for current month
- [ ] Both JSON and Markdown outputs created
- [ ] Filenames increment on re-run

### Phase 3
- [ ] `-m 6` and `-q 2` work
- [ ] `-u otheruser` works
- [ ] Mutual exclusivity enforced

### Phase 4
- [ ] Config file loading works
- [ ] Environment variables override config
- [ ] CLI overrides everything

### Phase 5
- [ ] Logs written to `logs/` directory
- [ ] Errors logged to `errors.log`
- [ ] Old logs cleaned up

### Phase 6
- [ ] JSON validates against schema
- [ ] 80% test coverage
- [ ] All tests pass

---

## Troubleshooting

### Common Issues

**"gh CLI not found"**
```bash
# Install GitHub CLI
brew install gh  # macOS
# Then authenticate
gh auth login
```

**"Permission denied on generate_report.py"**
```bash
chmod +x generate_report.py
```

**"Module not found"**
```bash
# Run from project root
cd .scripts/github-activity
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"Rate limit exceeded"**
- Increase `request_delay` in config
- Enable caching
- Use `--no-cache` only when needed

---

## Code Quality Checks

Before considering implementation complete:

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest -v --cov=src --cov-report=html

# Verify coverage
open htmlcov/index.html
```

---

*Document Version: 1.1*
*Last Updated: 2026-01-04*
*For use by: AI Implementation Agents*

---

## Changelog

### v1.1 (2026-01-04)
- Updated CLI code sample to match implementation:
  - Removed `-o/--orgs` (organizations is config-only)
  - Replaced `-v/--verbose` with `--log-level`
  - Replaced `--include-private`/`--include-forks` with `--include-repos`/`--exclude-repos`
  - Changed `-o` short form from orgs to output-dir
- Updated `commit_message_format` default from `"first_line"` to `"truncated"`
- Updated UC-5.1 to document new CLI options
