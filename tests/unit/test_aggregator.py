# =============================================================================
# FILE: tests/unit/test_aggregator.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for data aggregation.  # UC-13.1 | PLAN-4

Tests:
- AggregatedData dataclass
- DataAggregator class
- Filtering by date range
- Summary calculations
- Repository breakdown
"""
import pytest
from datetime import date
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.processors.aggregator import AggregatedData, DataAggregator


class TestAggregatedData:  # UC-13.1 | PLAN-4
    """Tests for AggregatedData dataclass."""

    def test_empty_aggregated_data(self):
        """Test empty AggregatedData has zero counts."""
        data = AggregatedData()

        assert data.total_commits == 0
        assert data.total_prs_opened == 0
        assert data.total_prs_merged == 0
        assert data.total_issues_opened == 0
        assert data.total_issues_closed == 0
        assert data.repos_contributed_to == 0

    def test_total_commits_count(self):
        """Test total_commits property."""
        data = AggregatedData(commits=[
            {"sha": "abc123", "date": "2024-12-15"},
            {"sha": "def456", "date": "2024-12-16"},
        ])

        assert data.total_commits == 2

    def test_total_prs_opened(self):
        """Test total_prs_opened property."""
        data = AggregatedData(pull_requests=[
            {"number": 1, "created_at": "2024-12-15"},
            {"number": 2, "created_at": "2024-12-16"},
            {"number": 3, "created_at": "2024-12-17"},
        ])

        assert data.total_prs_opened == 3

    def test_total_prs_merged(self):
        """Test total_prs_merged counts only merged PRs."""
        data = AggregatedData(pull_requests=[
            {"number": 1, "merged_at": "2024-12-15T10:00:00Z"},
            {"number": 2, "merged_at": None},
            {"number": 3, "merged_at": "2024-12-16T10:00:00Z"},
        ])

        assert data.total_prs_merged == 2

    def test_total_issues_closed(self):
        """Test total_issues_closed counts only closed issues."""
        data = AggregatedData(issues=[
            {"number": 1, "state": "closed"},
            {"number": 2, "state": "open"},
            {"number": 3, "state": "closed"},
        ])

        assert data.total_issues_closed == 2
        assert data.total_issues_opened == 3

    def test_repos_contributed_to(self):
        """Test repos_contributed_to count."""
        data = AggregatedData(repositories=["org/repo1", "org/repo2"])

        assert data.repos_contributed_to == 2

    def test_get_summary(self):
        """Test get_summary returns dict with all fields."""
        data = AggregatedData(
            commits=[{"sha": "abc", "date": "2024-12-15", "repository": "org/repo1"}],
            pull_requests=[{"number": 1, "created_at": "2024-12-15", "merged_at": "2024-12-16", "repository": "org/repo1"}],
            issues=[{"number": 1, "state": "open", "created_at": "2024-12-15", "repository": "org/repo1"}],
            reviews=[{"pr_number": 1}],
            comments=[{"id": 1, "created_at": "2024-12-15"}],
            repositories=["org/repo1"]
        )

        summary = data.get_summary()

        assert "total_commits" in summary
        assert "total_prs_opened" in summary
        assert "total_prs_merged" in summary
        assert "total_issues_opened" in summary
        assert "total_issues_closed" in summary
        assert "repos_contributed_to" in summary
        assert summary["total_commits"] == 1

    def test_most_active_day(self):
        """Test most active day calculation."""
        data = AggregatedData(
            commits=[
                {"date": "2024-12-15"},
                {"date": "2024-12-15"},
                {"date": "2024-12-16"},
            ]
        )

        summary = data.get_summary()
        assert summary["most_active_day"] == "2024-12-15"

    def test_most_active_repo(self):
        """Test most active repository calculation."""
        data = AggregatedData(
            commits=[
                {"repository": "org/repo1"},
                {"repository": "org/repo1"},
                {"repository": "org/repo2"},
            ]
        )

        summary = data.get_summary()
        assert summary["most_active_repo"] == "org/repo1"


class TestDataAggregator:  # UC-13.1 | PLAN-4
    """Tests for DataAggregator class."""

    def test_init(self):
        """Test DataAggregator initialization."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert aggregator.username == "testuser"
        assert aggregator.start_date == date(2024, 12, 1)
        assert aggregator.end_date == date(2024, 12, 31)

    def test_aggregate_empty_data(self):
        """Test aggregation with empty data."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        result = aggregator.aggregate()

        assert isinstance(result, AggregatedData)
        assert result.total_commits == 0

    def test_aggregate_filters_by_date(self):
        """Test that aggregation filters by date range."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        commits = [
            {"sha": "abc", "date": "2024-11-30"},  # Before range
            {"sha": "def", "date": "2024-12-15"},  # In range
            {"sha": "ghi", "date": "2025-01-01"},  # After range
        ]

        result = aggregator.aggregate(commits=commits)

        assert result.total_commits == 1
        assert result.commits[0]["sha"] == "def"

    def test_aggregate_with_all_data_types(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Test aggregation with all data types."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        result = aggregator.aggregate(
            commits=sample_commits,
            pull_requests=sample_pull_requests,
            issues=sample_issues,
            reviews=sample_reviews,
            comments=[]
        )

        assert isinstance(result, AggregatedData)
        assert result.username == "testuser"

    def test_aggregate_collects_repositories(self):
        """Test that aggregation collects unique repositories."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        commits = [
            {"sha": "abc", "date": "2024-12-15", "repository": "org/repo1"},
            {"sha": "def", "date": "2024-12-16", "repository": "org/repo2"},
            {"sha": "ghi", "date": "2024-12-17", "repository": "org/repo1"},
        ]

        result = aggregator.aggregate(commits=commits)

        assert len(result.repositories) == 2
        assert "org/repo1" in result.repositories
        assert "org/repo2" in result.repositories

    def test_get_repo_breakdown(self):
        """Test repository breakdown calculation."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        data = AggregatedData(
            commits=[
                {"repository": "org/repo1"},
                {"repository": "org/repo1"},
                {"repository": "org/repo2"},
            ],
            pull_requests=[
                {"repository": "org/repo1"},
            ],
            issues=[
                {"repository": "org/repo2"},
            ],
            reviews=[],
            repositories=["org/repo1", "org/repo2"]
        )

        breakdown = aggregator.get_repo_breakdown(data)

        assert len(breakdown) == 2

        repo1 = next(r for r in breakdown if r["name"] == "org/repo1")
        assert repo1["commits"] == 2
        assert repo1["prs"] == 1
        assert repo1["issues"] == 0

        repo2 = next(r for r in breakdown if r["name"] == "org/repo2")
        assert repo2["commits"] == 1
        assert repo2["issues"] == 1

    def test_aggregate_ignores_extra_kwargs(self):
        """Test that extra kwargs like 'events' don't cause errors."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        # Should not raise an error
        result = aggregator.aggregate(
            commits=[],
            events=[{"id": "event1"}],  # Extra kwarg
            unknown_key=[]  # Another extra kwarg
        )

        assert isinstance(result, AggregatedData)
