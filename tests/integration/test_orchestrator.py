# =============================================================================
# FILE: tests/integration/test_orchestrator.py
# TASKS: UC-13.2
# PLAN: Section 4
# =============================================================================
"""
Integration tests for full pipeline orchestrator.  # UC-13.2 | PLAN-4

Tests the complete report generation pipeline with mocked components.

Tests:
- Full pipeline execution
- Error handling
- Output generation
"""
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.processors.aggregator import DataAggregator, AggregatedData


class TestPipelineIntegration:  # UC-13.2 | PLAN-4
    """Integration tests for the report generation pipeline."""

    @pytest.fixture
    def mock_fetchers(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews, sample_events):
        """Create mock fetchers returning fixture data."""
        event_fetcher = MagicMock()
        event_fetcher.fetch.return_value = sample_events

        commit_fetcher = MagicMock()
        commit_fetcher.fetch.return_value = sample_commits

        pr_fetcher = MagicMock()
        pr_fetcher.fetch.return_value = sample_pull_requests

        issue_fetcher = MagicMock()
        issue_fetcher.fetch.return_value = sample_issues

        review_fetcher = MagicMock()
        review_fetcher.fetch.return_value = sample_reviews

        return {
            "events": event_fetcher,
            "commits": commit_fetcher,
            "pull_requests": pr_fetcher,
            "issues": issue_fetcher,
            "reviews": review_fetcher,
        }

    def test_aggregation_pipeline(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Test data aggregation in the pipeline."""
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
        assert result.start_date == date(2024, 12, 1)

    def test_pipeline_with_empty_data(self):
        """Test pipeline handles empty data gracefully."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        result = aggregator.aggregate(
            commits=[],
            pull_requests=[],
            issues=[],
            reviews=[],
            comments=[]
        )

        assert result.total_commits == 0
        assert result.total_prs_opened == 0
        assert result.total_issues_opened == 0

    def test_pipeline_summary_calculation(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Test summary calculation in pipeline."""
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

        summary = result.get_summary()

        assert "total_commits" in summary
        assert "total_prs_opened" in summary
        assert "total_prs_merged" in summary
        assert "total_issues_opened" in summary
        assert "repos_contributed_to" in summary

    def test_pipeline_repository_breakdown(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Test repository breakdown calculation."""
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

        breakdown = aggregator.get_repo_breakdown(result)

        assert isinstance(breakdown, list)
        for repo in breakdown:
            assert "name" in repo
            assert "commits" in repo
            assert "prs" in repo
            assert "issues" in repo


class TestPipelineErrorHandling:  # UC-13.2 | PLAN-4
    """Test error handling in the pipeline."""

    def test_handles_none_data(self):
        """Test pipeline handles None data."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        result = aggregator.aggregate(
            commits=None,
            pull_requests=None,
            issues=None,
            reviews=None,
            comments=None
        )

        # Should not raise, should return empty data
        assert result.total_commits == 0

    def test_handles_malformed_dates(self):
        """Test pipeline handles malformed date data."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        commits = [
            {"sha": "abc123", "date": "invalid-date"},
            {"sha": "def456", "date": "2024-12-15"},
        ]

        result = aggregator.aggregate(commits=commits)

        # Should not crash, should skip invalid dates
        assert isinstance(result, AggregatedData)


class TestPipelineWithConfig:  # UC-13.2 | PLAN-4
    """Test pipeline with configuration."""

    def test_pipeline_respects_date_range(self, sample_config):
        """Test that pipeline respects date range configuration."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 15),
            end_date=date(2024, 12, 20)
        )

        commits = [
            {"sha": "before", "date": "2024-12-10"},  # Before range
            {"sha": "in_range", "date": "2024-12-16"},  # In range
            {"sha": "after", "date": "2024-12-25"},  # After range
        ]

        result = aggregator.aggregate(commits=commits)

        # Only one commit should be in range
        assert result.total_commits == 1
        assert result.commits[0]["sha"] == "in_range"

    def test_pipeline_collects_unique_repos(self, sample_config):
        """Test that pipeline collects unique repositories."""
        aggregator = DataAggregator(
            username="testuser",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        commits = [
            {"sha": "a", "date": "2024-12-15", "repository": "org/repo1"},
            {"sha": "b", "date": "2024-12-16", "repository": "org/repo1"},
            {"sha": "c", "date": "2024-12-17", "repository": "org/repo2"},
        ]

        result = aggregator.aggregate(commits=commits)

        assert len(result.repositories) == 2
        assert "org/repo1" in result.repositories
        assert "org/repo2" in result.repositories
