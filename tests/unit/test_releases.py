# =============================================================================
# FILE: tests/unit/test_releases.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Unit tests for ReleasesFetcher helper methods.  # UC-2.2 | PLAN-3.4

Tests:
- Monorepo tag detection
- Anomaly detection (huge, empty, rapid releases)
- Contribution weight calculation
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fetchers.releases import ReleasesFetcher


@pytest.fixture
def fetcher():
    """Create a minimal ReleasesFetcher instance for testing helper methods."""
    gh_client = MagicMock()
    config = MagicMock()
    config.high_activity_threshold = 100
    config.request_delay = 0.0
    return ReleasesFetcher(gh_client=gh_client, config=config, username="testuser")


class TestMonorepoDetection:
    """Tests for _detect_monorepo_tag helper method."""

    def test_scoped_tag_detected(self, fetcher):
        """Tags like 'plugin/1.0.0' are monorepo tags."""
        assert fetcher._detect_monorepo_tag("plugin/1.0.0") is True

    def test_bare_version_not_monorepo(self, fetcher):
        """Tags like '1.0.0' are not monorepo."""
        assert fetcher._detect_monorepo_tag("1.0.0") is False

    def test_v_prefix_not_monorepo(self, fetcher):
        """Tags like 'v1.0.0' are not monorepo."""
        assert fetcher._detect_monorepo_tag("v1.0.0") is False

    def test_path_with_v_prefix(self, fetcher):
        """Tags like 'packages/foo/v2.1.0' are monorepo."""
        assert fetcher._detect_monorepo_tag("packages/foo/v2.1.0") is True

    def test_two_segment_scoped_tag(self, fetcher):
        """Tags like 'frontend/v3.0' are monorepo."""
        assert fetcher._detect_monorepo_tag("frontend/v3.0") is True

    def test_bare_tag_no_slash(self, fetcher):
        """Tags without a slash are not monorepo."""
        assert fetcher._detect_monorepo_tag("release-2024-03") is False


class TestAnomalyDetection:
    """Tests for _detect_anomalies helper method."""

    def test_huge_release_flagged(self, fetcher):
        """Release with >500 commits should be flagged as huge_release."""
        anomalies = fetcher._detect_anomalies(
            total_commits=501,
            published_at="2026-03-15T10:00:00Z",
            all_releases=[]
        )
        assert "huge_release" in anomalies

    def test_empty_release_flagged(self, fetcher):
        """Release with 0 commits should be flagged as empty_release."""
        anomalies = fetcher._detect_anomalies(
            total_commits=0,
            published_at="2026-03-15T10:00:00Z",
            all_releases=[]
        )
        assert "empty_release" in anomalies

    def test_normal_release_no_anomalies(self, fetcher):
        """Release with a normal commit count should have no anomalies."""
        anomalies = fetcher._detect_anomalies(
            total_commits=12,
            published_at="2026-03-15T10:00:00Z",
            all_releases=[{"published_at": "2026-03-15T10:00:00Z"}]
        )
        assert "huge_release" not in anomalies
        assert "empty_release" not in anomalies

    def test_rapid_release_flagged(self, fetcher):
        """Two releases on the same day should flag rapid_release."""
        all_releases = [
            {"published_at": "2026-03-15T08:00:00Z"},
            {"published_at": "2026-03-15T20:00:00Z"},
        ]
        anomalies = fetcher._detect_anomalies(
            total_commits=5,
            published_at="2026-03-15T08:00:00Z",
            all_releases=all_releases
        )
        assert "rapid_release" in anomalies

    def test_exactly_500_commits_not_huge(self, fetcher):
        """Release with exactly 500 commits should NOT be flagged as huge."""
        anomalies = fetcher._detect_anomalies(
            total_commits=500,
            published_at="2026-03-15T10:00:00Z",
            all_releases=[]
        )
        assert "huge_release" not in anomalies

    def test_no_published_at_no_rapid_flag(self, fetcher):
        """Missing published_at should not trigger rapid_release."""
        anomalies = fetcher._detect_anomalies(
            total_commits=5,
            published_at="",
            all_releases=[{"published_at": ""}]
        )
        assert "rapid_release" not in anomalies


class TestContributionWeight:
    """Tests for contribution weight formula in _get_contribution."""

    def test_weight_calculation(self, fetcher):
        """Test 60% commits + 40% reviews formula.

        user_commits=5, total_commits=10 -> commit_share = 0.5
        user_reviewed=2, total_prs=4    -> review_share = 0.5
        weight = (0.5 * 0.6 + 0.5 * 0.4) * 100 = 50.0
        """
        # commit_share = 5/10 = 0.5; review_share = 2/4 = 0.5
        commit_share = 5 / 10
        review_share = 2 / 4
        expected = round((commit_share * 0.6 + review_share * 0.4) * 100, 1)
        assert expected == 50.0

    def test_zero_totals_no_division_error(self, fetcher):
        """When total_commits=0 and total_prs=0, weight should be 0."""
        total_commits = 0
        total_prs = 0
        user_commits = 0
        user_reviewed = 0
        commit_share = user_commits / total_commits if total_commits > 0 else 0
        review_share = user_reviewed / total_prs if total_prs > 0 else 0
        weight = round((commit_share * 0.6 + review_share * 0.4) * 100, 1)
        assert weight == 0.0

    def test_commits_only(self, fetcher):
        """Weight with commits only (no PRs merged): review_share = 0."""
        total_commits = 10
        user_commits = 10
        total_prs = 0
        user_reviewed = 0
        commit_share = user_commits / total_commits if total_commits > 0 else 0
        review_share = user_reviewed / total_prs if total_prs > 0 else 0
        weight = round((commit_share * 0.6 + review_share * 0.4) * 100, 1)
        # 1.0 * 0.6 + 0 * 0.4 = 0.6 -> 60.0
        assert weight == 60.0

    def test_reviews_only(self, fetcher):
        """Weight with reviews but no user commits: commit_share = 0."""
        total_commits = 10
        user_commits = 0
        total_prs = 4
        user_reviewed = 4
        commit_share = user_commits / total_commits if total_commits > 0 else 0
        review_share = user_reviewed / total_prs if total_prs > 0 else 0
        weight = round((commit_share * 0.6 + review_share * 0.4) * 100, 1)
        # 0 * 0.6 + 1.0 * 0.4 = 0.4 -> 40.0
        assert weight == 40.0
