# =============================================================================
# FILE: src/processors/metrics.py
# TASKS: UC-7.1
# PLAN: Section 3.7
# =============================================================================
"""
Metrics Calculator.

This module calculates various activity metrics from aggregated data:

PR Metrics (UC-7.1):
- Average commits per PR
- Average time to merge
- Average time to first review
- Review iterations count
- PRs merged without changes
- PRs with requested changes

Review Metrics (UC-7.1):
- Average review turnaround time
- Reviews with comments count
- Approvals count
- Changes requested count

Engagement Metrics (UC-7.1):
- Average response time
- Comment to code ratio
- Collaboration score

Productivity Patterns (UC-7.1):
- Activity by day of week
- Activity by hour of day
- Most active repositories

Reaction Breakdown:
- Count by reaction type
- Most reacted content
"""
# UC-7.1, UC-7.1, UC-7.1 | PLAN-3.7

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.config.settings import MetricsConfig


@dataclass
class PRMetrics:  # UC-7.1 | PLAN-3.7.1
    """
    Calculated PR metrics.

    All metrics from Plan Section 3.7.1 PR Metrics table.
    """

    avg_commits_per_pr: float = 0.0  # sum(commits) / count(prs)
    avg_time_to_merge_hours: float = 0.0  # avg(merged_at - created_at)
    avg_time_to_first_review_hours: float = 0.0  # avg(first_review_at - created_at)
    avg_review_iterations: float = 0.0  # avg(count of review rounds per PR)
    prs_merged_without_changes: int = 0  # count(prs approved on first review)
    prs_with_requested_changes: int = 0  # count(prs with "changes_requested")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_commits_per_pr": round(self.avg_commits_per_pr, 2),
            "avg_time_to_merge_hours": round(self.avg_time_to_merge_hours, 2),
            "avg_time_to_first_review_hours": round(self.avg_time_to_first_review_hours, 2),
            "avg_review_iterations": round(self.avg_review_iterations, 2),
            "prs_merged_without_changes": self.prs_merged_without_changes,
            "prs_with_requested_changes": self.prs_with_requested_changes,
        }


@dataclass
class ReviewMetrics:  # UC-7.1 | PLAN-3.7.1
    """
    Calculated review metrics.

    All metrics from Plan Section 3.7.1 Review Metrics table.
    """

    avg_review_turnaround_hours: float = 0.0  # avg(review_submitted - review_requested)
    reviews_with_comments: int = 0  # count(reviews where body.length > 0)
    approvals: int = 0  # count(reviews where state == "APPROVED")
    changes_requested: int = 0  # count(reviews where state == "CHANGES_REQUESTED")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_review_turnaround_hours": round(self.avg_review_turnaround_hours, 2),
            "reviews_with_comments": self.reviews_with_comments,
            "approvals": self.approvals,
            "changes_requested": self.changes_requested,
        }


@dataclass
class EngagementMetrics:  # UC-7.1 | PLAN-3.7.1
    """
    Calculated engagement metrics.

    All metrics from Plan Section 3.7.1 Engagement Metrics table.
    """

    avg_response_time_hours: float = 0.0  # avg(time between comment and reply)
    comment_to_code_ratio: float = 0.0  # total_comments / total_commits
    collaboration_score: float = 0.0  # weighted(reviews + comments + reactions)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_response_time_hours": round(self.avg_response_time_hours, 2),
            "comment_to_code_ratio": round(self.comment_to_code_ratio, 2),
            "collaboration_score": round(self.collaboration_score, 2),
        }


@dataclass
class ProductivityPatterns:  # UC-7.1 | PLAN-3.7.1
    """
    Productivity patterns by time of day and day of week.
    """

    by_day: dict[str, int] = field(default_factory=lambda: {
        "Monday": 0,
        "Tuesday": 0,
        "Wednesday": 0,
        "Thursday": 0,
        "Friday": 0,
        "Saturday": 0,
        "Sunday": 0,
    })
    by_hour: dict[str, int] = field(default_factory=lambda: {
        str(h): 0 for h in range(24)
    })
    most_active_day: str = ""
    most_active_hour: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "by_day": self.by_day,
            "by_hour": self.by_hour,
            "most_active_day": self.most_active_day,
            "most_active_hour": self.most_active_hour,
        }


@dataclass
class ReactionBreakdown:  # UC-7.1 | PLAN-3.7.1
    """
    Reaction emoji breakdown.
    """

    counts: dict[str, int] = field(default_factory=dict)
    total: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "counts": self.counts,
            "total": self.total,
        }


class MetricsCalculator:  # UC-7.1, UC-7.1, UC-7.1 | PLAN-3.7.3
    """
    Calculate advanced metrics from activity data.

    Calculates all metrics defined in Plan Section 3.7 based on
    the configuration flags in MetricsConfig.

    Attributes:
        config: MetricsConfig with flags for each metric type
    """

    def __init__(self, config: MetricsConfig) -> None:
        """
        Initialize the metrics calculator.

        Args:
            config: MetricsConfig instance with metric calculation flags
        """
        self.config = config

    def calculate_pr_metrics(
        self,
        prs: list[dict[str, Any]],
        reviews: list[dict[str, Any]] | None = None,
        reviews_on_authored_prs: list[dict[str, Any]] | None = None
    ) -> PRMetrics | None:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate PR-related metrics.

        Calculates all 6 PR metrics from Plan Section 3.7.1:
        - avg_commits_per_pr
        - avg_time_to_merge_hours
        - avg_time_to_first_review_hours
        - avg_review_iterations
        - prs_merged_without_changes
        - prs_with_requested_changes

        Args:
            prs: List of pull request dictionaries
            reviews: Optional list of review dictionaries for review-related metrics
            reviews_on_authored_prs: Reviews by others on user's PRs (for changes requested)

        Returns:
            PRMetrics instance if pr_metrics enabled and prs exist, None otherwise
        """
        if not self.config.pr_metrics or not prs:
            return None

        metrics = PRMetrics()

        # Calculate average commits per PR
        total_commits = sum(pr.get("commits_count", pr.get("commits", 0)) for pr in prs)
        metrics.avg_commits_per_pr = total_commits / len(prs)

        # Calculate average time to merge
        merge_times: list[float] = []
        for pr in prs:
            merged_at = pr.get("merged_at")
            created_at = pr.get("created_at")
            if merged_at and created_at:
                try:
                    created = self._parse_datetime(created_at)
                    merged = self._parse_datetime(merged_at)
                    hours = (merged - created).total_seconds() / 3600
                    merge_times.append(hours)
                except (ValueError, TypeError):
                    pass

        if merge_times:
            metrics.avg_time_to_merge_hours = sum(merge_times) / len(merge_times)

        # Use reviews_on_authored_prs for first review time and changes requested
        # These are reviews FROM others ON the user's PRs
        reviews_to_use = reviews_on_authored_prs if reviews_on_authored_prs else reviews

        if reviews_to_use:
            first_review_times: list[float] = []
            # Group reviews by PR
            reviews_by_pr: dict[str, list[dict]] = {}
            for review in reviews_to_use:
                pr_key = f"{review.get('repository', '')}#{review.get('pr_number', '')}"
                if pr_key not in reviews_by_pr:
                    reviews_by_pr[pr_key] = []
                reviews_by_pr[pr_key].append(review)

            for pr in prs:
                pr_key = f"{pr.get('repository', '')}#{pr.get('number', '')}"
                pr_reviews = reviews_by_pr.get(pr_key, [])
                if pr_reviews:
                    # Find first review
                    pr_reviews_sorted = sorted(
                        pr_reviews,
                        key=lambda r: r.get("submitted_at", "")
                    )
                    first_review = pr_reviews_sorted[0]
                    created_at = pr.get("created_at")
                    submitted_at = first_review.get("submitted_at")
                    if created_at and submitted_at:
                        try:
                            created = self._parse_datetime(created_at)
                            reviewed = self._parse_datetime(submitted_at)
                            hours = (reviewed - created).total_seconds() / 3600
                            if hours >= 0:  # Sanity check
                                first_review_times.append(hours)
                        except (ValueError, TypeError):
                            pass

            if first_review_times:
                metrics.avg_time_to_first_review_hours = (
                    sum(first_review_times) / len(first_review_times)
                )

            # Calculate review iterations and changes requested stats
            for pr in prs:
                pr_key = f"{pr.get('repository', '')}#{pr.get('number', '')}"
                pr_reviews = reviews_by_pr.get(pr_key, [])

                if pr_reviews:
                    # Count unique review rounds (by reviewer)
                    # Handle both dict and string formats for user
                    def get_reviewer(r: dict) -> str:
                        user = r.get("user", "")
                        if isinstance(user, dict):
                            return user.get("login", "")
                        return user if isinstance(user, str) else ""
                    reviewers = set(get_reviewer(r) for r in pr_reviews)
                    metrics.avg_review_iterations += len(reviewers)

                    # Check for changes requested
                    has_changes_requested = any(
                        r.get("state") == "CHANGES_REQUESTED" for r in pr_reviews
                    )
                    if has_changes_requested:
                        metrics.prs_with_requested_changes += 1
                    elif pr.get("merged_at"):
                        # Merged without changes requested
                        metrics.prs_merged_without_changes += 1

            if len(prs) > 0:
                metrics.avg_review_iterations /= len(prs)

        return metrics

    def calculate_review_metrics(
        self,
        reviews: list[dict[str, Any]],
        prs: list[dict[str, Any]] | None = None
    ) -> ReviewMetrics | None:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate review-related metrics.

        Calculates all 4 review metrics from Plan Section 3.7.1:
        - avg_review_turnaround_hours
        - reviews_with_comments
        - approvals
        - changes_requested

        Args:
            reviews: List of review dictionaries
            prs: Optional list of PRs to calculate review turnaround from PR created_at

        Returns:
            ReviewMetrics instance if review_metrics enabled and reviews exist
        """
        if not self.config.review_metrics or not reviews:
            return None

        metrics = ReviewMetrics()

        turnaround_times: list[float] = []

        # Build PR lookup by key for turnaround calculation
        prs_by_key: dict[str, dict] = {}
        if prs:
            for pr in prs:
                pr_key = f"{pr.get('repository', '')}#{pr.get('number', '')}"
                prs_by_key[pr_key] = pr

        for review in reviews:
            # Count by state
            state = review.get("state", "")
            if state == "APPROVED":
                metrics.approvals += 1
            elif state == "CHANGES_REQUESTED":
                metrics.changes_requested += 1

            # Count reviews with comments
            body_length = review.get("body_length", 0)
            if body_length is None:
                body = review.get("body", "")
                body_length = len(body) if body else 0
            if body_length > 0:
                metrics.reviews_with_comments += 1

            # Calculate turnaround time from PR created_at to review submitted_at
            submitted_at = review.get("submitted_at")
            if submitted_at:
                # Try to get PR created_at for turnaround calculation
                pr_key = f"{review.get('repository', '')}#{review.get('pr_number', '')}"
                pr = prs_by_key.get(pr_key)
                pr_created_at = pr.get("created_at") if pr else review.get("requested_at")

                if pr_created_at:
                    try:
                        created = self._parse_datetime(pr_created_at)
                        submitted = self._parse_datetime(submitted_at)
                        hours = (submitted - created).total_seconds() / 3600
                        if hours >= 0:
                            turnaround_times.append(hours)
                    except (ValueError, TypeError):
                        pass

        if turnaround_times:
            metrics.avg_review_turnaround_hours = (
                sum(turnaround_times) / len(turnaround_times)
            )

        return metrics

    def calculate_engagement_metrics(
        self,
        commits: list[dict[str, Any]],
        comments: list[dict[str, Any]],
        reviews: list[dict[str, Any]] | None = None,
        reactions: list[dict[str, Any]] | None = None
    ) -> EngagementMetrics | None:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate engagement-related metrics.

        Calculates all 3 engagement metrics from Plan Section 3.7.1:
        - avg_response_time_hours
        - comment_to_code_ratio
        - collaboration_score

        Args:
            commits: List of commit dictionaries
            comments: List of comment dictionaries
            reviews: Optional list of review dictionaries
            reactions: Optional list of reaction dictionaries

        Returns:
            EngagementMetrics instance if engagement_metrics enabled
        """
        if not self.config.engagement_metrics:
            return None

        metrics = EngagementMetrics()

        # Calculate comment to code ratio
        if commits:
            metrics.comment_to_code_ratio = len(comments) / len(commits)

        # Calculate average response time
        # Group comments by issue/PR to find response times
        response_times: list[float] = []
        comments_by_thread: dict[str, list[dict]] = {}

        for comment in comments:
            thread_key = f"{comment.get('repository', '')}#{comment.get('issue_number', '')}"
            if thread_key not in comments_by_thread:
                comments_by_thread[thread_key] = []
            comments_by_thread[thread_key].append(comment)

        # Calculate time between consecutive comments as response time
        for thread_comments in comments_by_thread.values():
            sorted_comments = sorted(
                thread_comments,
                key=lambda c: c.get("created_at", "")
            )
            for i in range(1, len(sorted_comments)):
                prev_time = sorted_comments[i - 1].get("created_at")
                curr_time = sorted_comments[i].get("created_at")
                if prev_time and curr_time:
                    try:
                        prev = self._parse_datetime(prev_time)
                        curr = self._parse_datetime(curr_time)
                        hours = (curr - prev).total_seconds() / 3600
                        if 0 <= hours <= 168:  # Within a week
                            response_times.append(hours)
                    except (ValueError, TypeError):
                        pass

        if response_times:
            metrics.avg_response_time_hours = sum(response_times) / len(response_times)

        # Calculate collaboration score
        # Weighted formula: reviews * 3 + comments * 1 + reactions * 0.5
        review_count = len(reviews) if reviews else 0
        comment_count = len(comments)
        reaction_count = len(reactions) if reactions else 0

        metrics.collaboration_score = (
            review_count * 3.0 +
            comment_count * 1.0 +
            reaction_count * 0.5
        )

        return metrics

    def calculate_productivity_patterns(
        self,
        events: list[dict[str, Any]]
    ) -> ProductivityPatterns | None:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate productivity patterns by day of week and hour.

        Calculates activity distribution across:
        - 7 days of the week
        - 24 hours of the day

        Args:
            events: List of events with created_at timestamps

        Returns:
            ProductivityPatterns instance if productivity_patterns enabled
        """
        if not self.config.productivity_patterns or not events:
            return None

        patterns = ProductivityPatterns()

        for event in events:
            created_at = event.get("created_at")
            if not created_at:
                continue

            try:
                dt = self._parse_datetime(created_at)
                day_name = dt.strftime("%A")
                hour = str(dt.hour)

                if day_name in patterns.by_day:
                    patterns.by_day[day_name] += 1
                if hour in patterns.by_hour:
                    patterns.by_hour[hour] += 1
            except (ValueError, TypeError):
                pass

        # Find most active day and hour
        if patterns.by_day:
            patterns.most_active_day = max(
                patterns.by_day.items(),
                key=lambda x: x[1]
            )[0]

        if patterns.by_hour:
            most_active_hour_str = max(
                patterns.by_hour.items(),
                key=lambda x: x[1]
            )[0]
            patterns.most_active_hour = int(most_active_hour_str)

        return patterns

    def calculate_reaction_breakdown(
        self,
        reactions: list[dict[str, Any]]
    ) -> ReactionBreakdown | None:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate reaction emoji breakdown.

        Args:
            reactions: List of reaction dictionaries

        Returns:
            ReactionBreakdown instance if reaction_breakdown enabled
        """
        if not self.config.reaction_breakdown or not reactions:
            return None

        breakdown = ReactionBreakdown()

        for reaction in reactions:
            content = reaction.get("content", "unknown")
            if content not in breakdown.counts:
                breakdown.counts[content] = 0
            breakdown.counts[content] += 1
            breakdown.total += 1

        return breakdown

    def calculate_all(
        self,
        prs: list[dict[str, Any]],
        reviews: list[dict[str, Any]],
        commits: list[dict[str, Any]],
        comments: list[dict[str, Any]],
        events: list[dict[str, Any]],
        reactions: list[dict[str, Any]] | None = None,
        reviews_on_authored_prs: list[dict[str, Any]] | None = None,
        reviewed_prs: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:  # UC-7.1 | PLAN-3.7.3
        """
        Calculate all metrics and return as a dictionary.

        Convenience method that calculates all enabled metrics and
        returns them in a format ready for JSON serialization.

        Args:
            prs: List of pull request dictionaries (authored by user)
            reviews: List of review dictionaries (made by user)
            commits: List of commit dictionaries
            comments: List of comment dictionaries
            events: List of all events for productivity patterns
            reactions: Optional list of reactions
            reviews_on_authored_prs: Reviews by others on user's PRs
            reviewed_prs: PRs that the user reviewed (for review turnaround calc)

        Returns:
            Dictionary with all calculated metrics
        """
        result: dict[str, Any] = {}

        # PR Metrics - use reviews_on_authored_prs for changes requested
        pr_metrics = self.calculate_pr_metrics(prs, reviews, reviews_on_authored_prs)
        if pr_metrics:
            result["pr_metrics"] = pr_metrics.to_dict()

        # Review Metrics - pass reviewed_prs for turnaround calculation
        # If we don't have reviewed_prs, we can't calculate turnaround properly
        review_metrics = self.calculate_review_metrics(reviews, reviewed_prs)
        if review_metrics:
            result["review_metrics"] = review_metrics.to_dict()

        # Engagement Metrics
        engagement_metrics = self.calculate_engagement_metrics(
            commits, comments, reviews, reactions
        )
        if engagement_metrics:
            result["engagement_metrics"] = engagement_metrics.to_dict()

        # Productivity Patterns
        productivity = self.calculate_productivity_patterns(events)
        if productivity:
            result["productivity_by_day"] = productivity.by_day
            result["productivity_by_hour"] = productivity.by_hour

        # Reaction Breakdown
        if reactions:
            reaction_breakdown = self.calculate_reaction_breakdown(reactions)
            if reaction_breakdown:
                result["reaction_breakdown"] = reaction_breakdown.to_dict()

        return result

    def _parse_datetime(self, dt_string: str) -> datetime:  # UC-7.1 | PLAN-3.7.3
        """
        Parse ISO 8601 datetime string.

        Handles formats with or without trailing 'Z' and timezone info.

        Args:
            dt_string: ISO 8601 datetime string

        Returns:
            datetime object

        Raises:
            ValueError: If string cannot be parsed
        """
        # Remove trailing Z if present
        if dt_string.endswith("Z"):
            dt_string = dt_string[:-1]

        # Try parsing with and without microseconds
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(dt_string[:26], fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse datetime: {dt_string}")


def create_metrics_calculator(config: MetricsConfig) -> MetricsCalculator:
    """
    Factory function to create a MetricsCalculator instance.

    Args:
        config: MetricsConfig instance

    Returns:
        Configured MetricsCalculator instance
    """
    return MetricsCalculator(config)
