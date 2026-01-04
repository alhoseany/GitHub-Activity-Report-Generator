# =============================================================================
# FILE: tests/conftest.py
# TASKS: UC-13.1, UC-13.2
# PLAN: Section 4
# =============================================================================
"""
Shared pytest fixtures for GitHub Activity Report Generator tests.  # UC-13.1, UC-13.2 | PLAN-4

This module provides common fixtures used across unit, integration, and e2e tests:

Fixtures:
- sample_config: Sample configuration Settings object
- mock_github_client: Mock GitHubClient fixture
- sample_events: Sample events from fixtures
- sample_commits: Sample commits from fixtures
- sample_pull_requests: Sample PRs from fixtures
- sample_issues: Sample issues from fixtures
- sample_reviews: Sample reviews from fixtures
- temp_dir: Temporary directory fixture
- temp_cache_dir: Temporary cache directory
- temp_reports_dir: Temporary reports directory
- valid_report_data: Valid report data matching schema
- minimal_report_data: Minimal valid report data
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest

# Add src to path for imports
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# =============================================================================
# Directory Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def api_responses_dir(fixtures_dir: Path) -> Path:
    """Path to API responses fixtures directory."""
    return fixtures_dir / "api_responses"


@pytest.fixture
def expected_outputs_dir(fixtures_dir: Path) -> Path:
    """Path to expected outputs fixtures directory."""
    return fixtures_dir / "expected_outputs"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_cache_dir(temp_dir: Path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = temp_dir / ".cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def temp_reports_dir(temp_dir: Path) -> Path:
    """Create a temporary reports directory."""
    reports_dir = temp_dir / "reports"
    reports_dir.mkdir()
    return reports_dir


@pytest.fixture
def temp_logs_dir(temp_dir: Path) -> Path:
    """Create a temporary logs directory."""
    logs_dir = temp_dir / "logs"
    logs_dir.mkdir()
    return logs_dir


# =============================================================================
# Sample Data Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def sample_events(api_responses_dir: Path) -> list[dict[str, Any]]:
    """Load sample events from fixture file."""
    events_file = api_responses_dir / "events.json"
    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@pytest.fixture
def sample_commits(api_responses_dir: Path) -> list[dict[str, Any]]:
    """Load sample commits from fixture file."""
    commits_file = api_responses_dir / "commits.json"
    if commits_file.exists():
        with open(commits_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@pytest.fixture
def sample_pull_requests(api_responses_dir: Path) -> list[dict[str, Any]]:
    """Load sample pull requests from fixture file."""
    prs_file = api_responses_dir / "pull_requests.json"
    if prs_file.exists():
        with open(prs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@pytest.fixture
def sample_issues(api_responses_dir: Path) -> list[dict[str, Any]]:
    """Load sample issues from fixture file."""
    issues_file = api_responses_dir / "issues.json"
    if issues_file.exists():
        with open(issues_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@pytest.fixture
def sample_reviews(api_responses_dir: Path) -> list[dict[str, Any]]:
    """Load sample reviews from fixture file."""
    reviews_file = api_responses_dir / "reviews.json"
    if reviews_file.exists():
        with open(reviews_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@pytest.fixture
def sample_report(expected_outputs_dir: Path) -> dict[str, Any]:
    """Load sample expected report from fixture file."""
    report_file = expected_outputs_dir / "sample_report.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# =============================================================================
# Configuration Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def sample_config():
    """Create a sample Settings configuration object."""
    from src.config.settings import (
        Settings, PeriodConfig, UserConfig, RepositoryConfig,
        CacheConfig, OutputConfig, MetricsConfig, LoggingConfig,
        FetchingConfig, ReportCleanupConfig
    )

    return Settings(
        period=PeriodConfig(default_type="monthly"),
        user=UserConfig(username="testuser", organizations=[]),
        repositories=RepositoryConfig(
            include_private=True,
            include_forks=False,
            include=[],
            exclude=[]
        ),
        fetching=FetchingConfig(
            high_activity_threshold=100,
            request_delay=0.1,  # Faster for tests
            max_retries=2,
            timeout=10
        ),
        cache=CacheConfig(enabled=True, directory=".cache", ttl_hours=24),
        output=OutputConfig(
            directory="reports",
            formats=["json", "markdown"],
            include_links=True
        ),
        metrics=MetricsConfig(
            pr_metrics=True,
            review_metrics=True,
            engagement_metrics=True,
            productivity_patterns=True,
            reaction_breakdown=True
        ),
        logging=LoggingConfig(level="WARNING"),  # Reduce noise in tests
        output_cleanup=ReportCleanupConfig(enabled=False),  # Disable cleanup in tests
    )


@pytest.fixture
def cache_config():
    """Create a sample CacheConfig."""
    from src.config.settings import CacheConfig
    return CacheConfig(enabled=True, directory=".cache", ttl_hours=24)


@pytest.fixture
def metrics_config():
    """Create a sample MetricsConfig."""
    from src.config.settings import MetricsConfig
    return MetricsConfig(
        pr_metrics=True,
        review_metrics=True,
        engagement_metrics=True,
        productivity_patterns=True,
        reaction_breakdown=True
    )


@pytest.fixture
def disabled_cache_config():
    """Create a disabled CacheConfig."""
    from src.config.settings import CacheConfig
    return CacheConfig(enabled=False, directory=".cache", ttl_hours=24)


# =============================================================================
# Mock Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def mock_github_client(
    sample_events: list,
    sample_commits: list,
    sample_pull_requests: list,
    sample_issues: list,
    sample_reviews: list
):
    """Create a mock GitHubClient that returns fixture data."""
    client = MagicMock()

    # Configure mock methods to return fixture data
    client.fetch_events.return_value = sample_events
    client.fetch_commits.return_value = sample_commits
    client.fetch_pull_requests.return_value = sample_pull_requests
    client.fetch_issues.return_value = sample_issues
    client.fetch_reviews.return_value = sample_reviews

    # Configure properties
    client.username = "testuser"
    client.is_authenticated = True

    return client


@pytest.fixture
def empty_mock_github_client():
    """Create a mock GitHubClient that returns empty data."""
    client = MagicMock()

    client.fetch_events.return_value = []
    client.fetch_commits.return_value = []
    client.fetch_pull_requests.return_value = []
    client.fetch_issues.return_value = []
    client.fetch_reviews.return_value = []

    client.username = "testuser"
    client.is_authenticated = True

    return client


# =============================================================================
# Report Data Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def valid_report_data() -> dict[str, Any]:
    """Create valid report data matching the schema."""
    return {
        "metadata": {
            "generated_at": "2024-12-31T23:59:59Z",
            "user": {
                "login": "testuser",
                "id": 12345,
                "name": "Test User"
            },
            "period": {
                "type": "monthly",
                "year": 2024,
                "value": 12,
                "month": 12,
                "start_date": "2024-12-01",
                "end_date": "2024-12-31"
            },
            "schema_version": "1.0"
        },
        "summary": {
            "total_commits": 5,
            "total_prs_opened": 2,
            "total_prs_merged": 1,
            "total_prs_reviewed": 1,
            "total_issues_opened": 3,
            "total_issues_closed": 1,
            "total_comments": 2,
            "repos_contributed_to": 2
        },
        "activity": {
            "commits": [
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "repository": "testorg/test-repo",
                    "date": "2024-12-15T10:00:00Z"
                }
            ],
            "pull_requests": [
                {
                    "number": 42,
                    "title": "Test PR",
                    "repository": "testorg/test-repo",
                    "state": "merged",
                    "created_at": "2024-12-15T11:00:00Z"
                }
            ],
            "issues": [
                {
                    "number": 100,
                    "title": "Test Issue",
                    "repository": "testorg/test-repo",
                    "state": "open",
                    "created_at": "2024-12-15T12:00:00Z"
                }
            ],
            "reviews": [
                {
                    "id": 1001,
                    "pr_number": 55,
                    "repository": "testorg/another-repo",
                    "state": "APPROVED",
                    "submitted_at": "2024-12-15T13:00:00Z"
                }
            ],
            "comments": [
                {
                    "id": 2001,
                    "type": "issue_comment",
                    "repository": "testorg/test-repo",
                    "issue_number": 100,
                    "created_at": "2024-12-15T14:00:00Z"
                }
            ],
            "repositories": [
                {"name": "testorg/test-repo", "commits": 3, "prs": 2, "issues": 3, "reviews": 0},
                {"name": "testorg/another-repo", "commits": 2, "prs": 0, "issues": 0, "reviews": 1}
            ]
        }
    }


@pytest.fixture
def minimal_report_data() -> dict[str, Any]:
    """Create minimal valid report data with required fields only."""
    return {
        "metadata": {
            "generated_at": "2024-12-31T23:59:59Z",
            "user": {"login": "testuser"},
            "period": {
                "type": "monthly",
                "year": 2024,
                "start_date": "2024-12-01",
                "end_date": "2024-12-31"
            },
            "schema_version": "1.0"
        },
        "summary": {
            "total_commits": 0,
            "total_prs_opened": 0,
            "total_prs_merged": 0,
            "total_issues_opened": 0,
            "total_issues_closed": 0,
            "repos_contributed_to": 0
        },
        "activity": {
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "reviews": [],
            "comments": [],
            "repositories": []
        }
    }


@pytest.fixture
def invalid_report_data() -> dict[str, Any]:
    """Create invalid report data for testing validation errors."""
    return {
        "metadata": {
            # Missing required fields: generated_at, user, schema_version
            "period": {
                "type": "invalid_type",  # Invalid enum value
                "year": "2024",  # Should be integer
                "start_date": "2024-12-01"
                # Missing: end_date
            }
        },
        "summary": {
            # Missing all required fields
            "total_commits": "five"  # Should be integer
        }
        # Missing: activity section
    }


# =============================================================================
# Date Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def sample_date_range() -> tuple[date, date]:
    """Return a sample date range for December 2024."""
    return (date(2024, 12, 1), date(2024, 12, 31))


@pytest.fixture
def quarterly_date_range() -> tuple[date, date]:
    """Return a sample quarterly date range for Q4 2024."""
    return (date(2024, 10, 1), date(2024, 12, 31))


# =============================================================================
# Cleanup Config Fixtures  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

@pytest.fixture
def log_cleanup_config():
    """Create a LogCleanupConfig for testing."""
    from src.config.settings import LogCleanupConfig, ErrorLogCleanupConfig
    return LogCleanupConfig(
        trigger="manual",
        retention_days=7,
        max_files=10,
        max_size_mb=50,
        strategy="oldest_first",
        error_log=ErrorLogCleanupConfig(
            max_size_mb=5,
            max_files=3,
            max_age_days=7,
            compress_rotated=False
        )
    )


@pytest.fixture
def report_cleanup_config():
    """Create a ReportCleanupConfig for testing."""
    from src.config.settings import ReportCleanupConfig, ArchiveConfig
    return ReportCleanupConfig(
        enabled=True,
        keep_versions=2,
        retention_days=30,
        trigger="manual",
        archive=ArchiveConfig(
            enabled=False,  # Disable archive for simpler testing
            directory="reports/archive",
            compress=False
        )
    )


# =============================================================================
# Helper Functions  # UC-13.1, UC-13.2 | PLAN-4
# =============================================================================

def create_temp_json_file(temp_dir: Path, filename: str, data: dict | list) -> Path:
    """Helper to create a temporary JSON file with given data."""
    file_path = temp_dir / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path


def create_temp_report_files(reports_dir: Path, count: int = 3) -> list[Path]:
    """Helper to create multiple temporary report files for cleanup tests."""
    files = []
    for i in range(1, count + 1):
        for ext in ["json", "md"]:
            filename = f"2024-12-github-activity-{i}.{ext}"
            file_path = reports_dir / filename
            if ext == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"version": i}, f)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# Report v{i}\n")
            files.append(file_path)
    return files
