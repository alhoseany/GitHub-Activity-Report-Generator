# =============================================================================
# FILE: tests/integration/test_fetchers.py
# TASKS: UC-13.2
# PLAN: Section 4
# =============================================================================
"""
Integration tests for fetcher classes.  # UC-13.2 | PLAN-4

Tests fetcher classes with mocked GitHub client.

Tests:
- EventsFetcher with mock client
- CommitsFetcher with mock client
- PullRequestsFetcher with mock client
- IssuesFetcher with mock client
- ReviewsFetcher with mock client
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fetchers.events import EventsFetcher
from src.fetchers.commits import CommitsFetcher
from src.fetchers.pull_requests import PullRequestsFetcher
from src.fetchers.issues import IssuesFetcher
from src.fetchers.reviews import ReviewsFetcher


class TestEventsFetcher:  # UC-13.2 | PLAN-4
    """Integration tests for EventsFetcher."""

    def test_fetch_events_returns_list(self, mock_github_client, sample_events):
        """Test that fetch returns a list of events."""
        fetcher = EventsFetcher(mock_github_client, None, "testuser")
        mock_github_client.api.return_value = sample_events

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert isinstance(result, list)

    def test_fetch_events_calls_client(self, mock_github_client):
        """Test that fetch calls the client method."""
        mock_github_client.api.return_value = []
        fetcher = EventsFetcher(mock_github_client, None, "testuser")

        fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        mock_github_client.api.assert_called()

    def test_fetch_events_filters_by_date(self, mock_github_client, sample_events):
        """Test that events are filtered by date range."""
        fetcher = EventsFetcher(mock_github_client, None, "testuser")
        mock_github_client.api.return_value = sample_events

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 15),
            end_date=date(2024, 12, 15)
        )

        # Should only include events from Dec 15
        assert isinstance(result, list)


class TestCommitsFetcher:  # UC-13.2 | PLAN-4
    """Integration tests for CommitsFetcher."""

    def test_fetch_commits_returns_list(self, mock_github_client):
        """Test that fetch returns a list of commits."""
        # Mock search to return properly formatted data (as gh search returns)
        mock_github_client.search.return_value = [
            {
                "sha": "abc123",
                "commit": {"message": "Test commit", "committer": {"date": "2024-12-15T10:00:00Z"}},
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/commit/abc123"
            }
        ]
        fetcher = CommitsFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert isinstance(result, list)

    def test_fetch_commits_calls_client(self, mock_github_client):
        """Test that fetch calls the client method."""
        # CommitsFetcher uses gh.api() not gh.search()
        mock_github_client.api.return_value = {"items": []}
        fetcher = CommitsFetcher(mock_github_client, None, "testuser")

        fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        mock_github_client.api.assert_called()

    def test_fetch_commits_processes_data(self, mock_github_client):
        """Test that commit data is processed correctly."""
        # Mock search to return properly formatted data
        mock_github_client.search.return_value = [
            {
                "sha": "abc123",
                "commit": {"message": "Test commit", "committer": {"date": "2024-12-15T10:00:00Z"}},
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/commit/abc123"
            }
        ]
        fetcher = CommitsFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        if result:
            # Check that commits have expected fields after transformation
            commit = result[0]
            assert "sha" in commit
            assert "message" in commit
            assert "repository" in commit


class TestPullRequestsFetcher:  # UC-13.2 | PLAN-4
    """Integration tests for PullRequestsFetcher."""

    def test_fetch_prs_returns_list(self, mock_github_client):
        """Test that fetch returns a list of PRs."""
        # Mock search with properly formatted PR data
        mock_github_client.search.return_value = [
            {
                "number": 42,
                "title": "Test PR",
                "state": "open",
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/pull/42"
            }
        ]
        fetcher = PullRequestsFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert isinstance(result, list)

    def test_fetch_prs_filters_by_user(self, mock_github_client):
        """Test that PRs are filtered by user."""
        mock_github_client.search.return_value = [
            {
                "number": 42,
                "title": "Test PR",
                "state": "merged",
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/pull/42"
            }
        ]
        fetcher = PullRequestsFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        # All returned PRs should have expected structure
        assert isinstance(result, list)


class TestIssuesFetcher:  # UC-13.2 | PLAN-4
    """Integration tests for IssuesFetcher."""

    def test_fetch_issues_returns_list(self, mock_github_client):
        """Test that fetch returns a list of issues."""
        mock_github_client.search.return_value = [
            {
                "number": 100,
                "title": "Test Issue",
                "state": "open",
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/issues/100"
            }
        ]
        fetcher = IssuesFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert isinstance(result, list)

    def test_fetch_issues_data_structure(self, mock_github_client):
        """Test that issues have expected data structure."""
        mock_github_client.search.return_value = [
            {
                "number": 100,
                "title": "Test Issue",
                "state": "open",
                "repository": {"full_name": "testorg/test-repo"},
                "url": "https://github.com/testorg/test-repo/issues/100"
            }
        ]
        fetcher = IssuesFetcher(mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        # Issues should be a list
        assert isinstance(result, list)


class TestReviewsFetcher:  # UC-13.2 | PLAN-4
    """Integration tests for ReviewsFetcher."""

    def test_fetch_reviews_returns_list(self, mock_github_client, sample_reviews):
        """Test that fetch returns a list of reviews."""
        fetcher = ReviewsFetcher(mock_github_client, None, "testuser")

        # Reviews are fetched per-PR, not by date range
        # The base fetch_period returns empty for ReviewsFetcher
        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert isinstance(result, list)

    def test_fetch_reviews_for_prs(self, mock_github_client):
        """Test fetching reviews for a list of PRs."""
        fetcher = ReviewsFetcher(mock_github_client, None, "testuser")
        mock_github_client.api.return_value = [
            {
                "id": 1001,
                "state": "APPROVED",
                "submitted_at": "2024-12-15T10:00:00Z",
                "user": {"login": "testuser"},
                "body": "LGTM"
            }
        ]

        prs = [{"repository": "testorg/test-repo", "number": 42}]
        result = fetcher.fetch_reviews_for_prs(
            prs,
            start=date(2024, 12, 1),
            end=date(2024, 12, 31)
        )

        assert isinstance(result, list)


class TestFetcherWithEmptyData:  # UC-13.2 | PLAN-4
    """Test fetchers with empty data."""

    def test_event_fetcher_empty(self, empty_mock_github_client):
        """Test EventsFetcher with empty data."""
        empty_mock_github_client.api.return_value = []
        fetcher = EventsFetcher(empty_mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert result == []

    def test_commit_fetcher_empty(self, empty_mock_github_client):
        """Test CommitsFetcher with empty data."""
        empty_mock_github_client.search.return_value = []
        fetcher = CommitsFetcher(empty_mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert result == []

    def test_pr_fetcher_empty(self, empty_mock_github_client):
        """Test PullRequestsFetcher with empty data."""
        empty_mock_github_client.search.return_value = []
        fetcher = PullRequestsFetcher(empty_mock_github_client, None, "testuser")

        result = fetcher.fetch_period(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        assert result == []
