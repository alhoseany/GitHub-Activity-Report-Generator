# =============================================================================
# FILE: tests/unit/test_metrics.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for metrics calculation.  # UC-13.1 | PLAN-4

Tests:
- MetricsCalculator class
- PR metrics calculation
- Review metrics calculation
- Engagement metrics calculation
- Productivity patterns
- Reaction breakdown
"""
import pytest
from datetime import datetime
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.processors.metrics import (
    MetricsCalculator,
    PRMetrics,
    ReviewMetrics,
    EngagementMetrics,
    ProductivityPatterns,
    ReactionBreakdown,
    create_metrics_calculator,
)
from src.config.settings import MetricsConfig


class TestPRMetrics:  # UC-13.1 | PLAN-4
    """Tests for PRMetrics dataclass."""

    def test_default_values(self):
        """Test PRMetrics default values."""
        metrics = PRMetrics()

        assert metrics.avg_commits_per_pr == 0.0
        assert metrics.avg_time_to_merge_hours == 0.0
        assert metrics.prs_merged_without_changes == 0

    def test_to_dict(self):
        """Test PRMetrics to_dict conversion."""
        metrics = PRMetrics(
            avg_commits_per_pr=2.5,
            avg_time_to_merge_hours=24.0,
            prs_merged_without_changes=3
        )

        result = metrics.to_dict()

        assert result["avg_commits_per_pr"] == 2.5
        assert result["avg_time_to_merge_hours"] == 24.0
        assert result["prs_merged_without_changes"] == 3


class TestReviewMetrics:  # UC-13.1 | PLAN-4
    """Tests for ReviewMetrics dataclass."""

    def test_default_values(self):
        """Test ReviewMetrics default values."""
        metrics = ReviewMetrics()

        assert metrics.approvals == 0
        assert metrics.changes_requested == 0
        assert metrics.reviews_with_comments == 0

    def test_to_dict(self):
        """Test ReviewMetrics to_dict conversion."""
        metrics = ReviewMetrics(
            approvals=5,
            changes_requested=2,
            reviews_with_comments=7
        )

        result = metrics.to_dict()

        assert result["approvals"] == 5
        assert result["changes_requested"] == 2


class TestMetricsCalculator:  # UC-13.1 | PLAN-4
    """Tests for MetricsCalculator class."""

    @pytest.fixture
    def calculator(self, metrics_config):
        """Create a MetricsCalculator instance."""
        return MetricsCalculator(metrics_config)

    @pytest.fixture
    def disabled_calculator(self):
        """Create a MetricsCalculator with all metrics disabled."""
        config = MetricsConfig(
            pr_metrics=False,
            review_metrics=False,
            engagement_metrics=False,
            productivity_patterns=False,
            reaction_breakdown=False
        )
        return MetricsCalculator(config)

    def test_calculate_pr_metrics_empty(self, calculator):
        """Test PR metrics with empty data."""
        result = calculator.calculate_pr_metrics([])
        assert result is None

    def test_calculate_pr_metrics_disabled(self, disabled_calculator):
        """Test PR metrics when disabled."""
        prs = [{"number": 1, "commits_count": 5}]
        result = disabled_calculator.calculate_pr_metrics(prs)
        assert result is None

    def test_calculate_pr_metrics_avg_commits(self, calculator):
        """Test average commits per PR calculation."""
        prs = [
            {"number": 1, "commits_count": 2},
            {"number": 2, "commits_count": 4},
            {"number": 3, "commits_count": 6},
        ]

        result = calculator.calculate_pr_metrics(prs)

        assert result is not None
        assert result.avg_commits_per_pr == 4.0

    def test_calculate_pr_metrics_time_to_merge(self, calculator):
        """Test average time to merge calculation."""
        prs = [
            {
                "number": 1,
                "created_at": "2024-12-15T10:00:00Z",
                "merged_at": "2024-12-15T12:00:00Z"  # 2 hours
            },
            {
                "number": 2,
                "created_at": "2024-12-16T10:00:00Z",
                "merged_at": "2024-12-16T14:00:00Z"  # 4 hours
            },
        ]

        result = calculator.calculate_pr_metrics(prs)

        assert result is not None
        assert result.avg_time_to_merge_hours == 3.0

    def test_calculate_review_metrics_empty(self, calculator):
        """Test review metrics with empty data."""
        result = calculator.calculate_review_metrics([])
        assert result is None

    def test_calculate_review_metrics_disabled(self, disabled_calculator):
        """Test review metrics when disabled."""
        reviews = [{"id": 1, "state": "APPROVED"}]
        result = disabled_calculator.calculate_review_metrics(reviews)
        assert result is None

    def test_calculate_review_metrics_counts(self, calculator):
        """Test review metrics counting."""
        reviews = [
            {"id": 1, "state": "APPROVED", "body_length": 0},
            {"id": 2, "state": "APPROVED", "body_length": 50},
            {"id": 3, "state": "CHANGES_REQUESTED", "body_length": 100},
            {"id": 4, "state": "COMMENTED", "body_length": 25},
        ]

        result = calculator.calculate_review_metrics(reviews)

        assert result is not None
        assert result.approvals == 2
        assert result.changes_requested == 1
        assert result.reviews_with_comments == 3  # 3 have body_length > 0

    def test_calculate_engagement_metrics_empty(self, calculator):
        """Test engagement metrics with empty data."""
        result = calculator.calculate_engagement_metrics([], [])
        assert result is not None  # Should still calculate, just with zeros

    def test_calculate_engagement_metrics_disabled(self, disabled_calculator):
        """Test engagement metrics when disabled."""
        result = disabled_calculator.calculate_engagement_metrics([], [])
        assert result is None

    def test_calculate_engagement_metrics_ratio(self, calculator):
        """Test comment to code ratio calculation."""
        commits = [{"sha": "a"}, {"sha": "b"}, {"sha": "c"}]  # 3 commits
        comments = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}, {"id": 6}]  # 6 comments

        result = calculator.calculate_engagement_metrics(commits, comments)

        assert result is not None
        assert result.comment_to_code_ratio == 2.0

    def test_calculate_engagement_metrics_collaboration_score(self, calculator):
        """Test collaboration score calculation."""
        commits = []
        comments = [{"id": 1}, {"id": 2}]  # 2 comments * 1.0 = 2
        reviews = [{"id": 1}]  # 1 review * 3.0 = 3
        reactions = [{"id": 1}, {"id": 2}]  # 2 reactions * 0.5 = 1

        result = calculator.calculate_engagement_metrics(
            commits, comments, reviews, reactions
        )

        assert result is not None
        # score = 3 + 2 + 1 = 6
        assert result.collaboration_score == 6.0

    def test_calculate_productivity_patterns_empty(self, calculator):
        """Test productivity patterns with empty data."""
        result = calculator.calculate_productivity_patterns([])
        assert result is None

    def test_calculate_productivity_patterns_disabled(self, disabled_calculator):
        """Test productivity patterns when disabled."""
        events = [{"created_at": "2024-12-15T10:00:00Z"}]
        result = disabled_calculator.calculate_productivity_patterns(events)
        assert result is None

    def test_calculate_productivity_patterns_by_day(self, calculator):
        """Test productivity patterns by day of week."""
        # All on a Sunday (December 15, 2024)
        events = [
            {"created_at": "2024-12-15T10:00:00Z"},
            {"created_at": "2024-12-15T11:00:00Z"},
            {"created_at": "2024-12-15T12:00:00Z"},
        ]

        result = calculator.calculate_productivity_patterns(events)

        assert result is not None
        assert result.by_day["Sunday"] == 3
        assert result.most_active_day == "Sunday"

    def test_calculate_productivity_patterns_by_hour(self, calculator):
        """Test productivity patterns by hour."""
        events = [
            {"created_at": "2024-12-15T10:00:00Z"},
            {"created_at": "2024-12-15T10:30:00Z"},
            {"created_at": "2024-12-15T14:00:00Z"},
        ]

        result = calculator.calculate_productivity_patterns(events)

        assert result is not None
        assert result.by_hour["10"] == 2
        assert result.by_hour["14"] == 1
        assert result.most_active_hour == 10

    def test_calculate_reaction_breakdown_empty(self, calculator):
        """Test reaction breakdown with empty data."""
        result = calculator.calculate_reaction_breakdown([])
        assert result is None

    def test_calculate_reaction_breakdown_disabled(self, disabled_calculator):
        """Test reaction breakdown when disabled."""
        reactions = [{"content": "+1"}]
        result = disabled_calculator.calculate_reaction_breakdown(reactions)
        assert result is None

    def test_calculate_reaction_breakdown_counts(self, calculator):
        """Test reaction breakdown counting."""
        reactions = [
            {"content": "+1"},
            {"content": "+1"},
            {"content": "heart"},
            {"content": "rocket"},
        ]

        result = calculator.calculate_reaction_breakdown(reactions)

        assert result is not None
        assert result.counts["+1"] == 2
        assert result.counts["heart"] == 1
        assert result.counts["rocket"] == 1
        assert result.total == 4

    def test_calculate_all(self, calculator, sample_pull_requests, sample_reviews):
        """Test calculate_all method."""
        result = calculator.calculate_all(
            prs=sample_pull_requests,
            reviews=sample_reviews,
            commits=[],
            comments=[],
            events=[{"created_at": "2024-12-15T10:00:00Z"}],
            reactions=[]
        )

        assert isinstance(result, dict)
        # Should have some metrics present
        assert "pr_metrics" in result or len(sample_pull_requests) == 0


class TestCreateMetricsCalculator:  # UC-13.1 | PLAN-4
    """Tests for create_metrics_calculator factory function."""

    def test_creates_calculator(self, metrics_config):
        """Test factory function creates calculator."""
        calculator = create_metrics_calculator(metrics_config)

        assert isinstance(calculator, MetricsCalculator)
        assert calculator.config == metrics_config
