# =============================================================================
# FILE: src/processors/aggregator.py
# TASKS: UC-2.3, UC-7.1
# PLAN: Section 4.1, 3.7
# =============================================================================
"""
Data Aggregator.

This module provides data aggregation functionality:
- AggregatedData: Dataclass containing all activity data
- DataAggregator: Aggregates data from multiple fetchers

AggregatedData contains:
- commits: List of commit records
- pull_requests: List of PR records
- issues: List of issue records
- reviews: List of review records
- comments: List of comment records (from events)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class AggregatedData:  # UC-2.3 | PLAN-4.1
    """Container for all aggregated activity data."""
    commits: list[dict[str, Any]] = field(default_factory=list)
    pull_requests: list[dict[str, Any]] = field(default_factory=list)
    issues: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    start_date: date | None = None
    end_date: date | None = None
    username: str = ""
    repositories: list[str] = field(default_factory=list)

    @property
    def total_commits(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total number of commits."""
        return len(self.commits)

    @property
    def total_prs_opened(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total PRs opened (all PRs in the list)."""
        return len(self.pull_requests)

    @property
    def total_prs_merged(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total PRs merged."""
        return len([pr for pr in self.pull_requests if pr.get("merged_at")])

    @property
    def total_prs_reviewed(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total unique PRs reviewed."""
        return len(set(r.get("pr_number") for r in self.reviews if r.get("pr_number")))

    @property
    def total_issues_opened(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total issues opened."""
        return len(self.issues)

    @property
    def total_issues_closed(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total issues closed."""
        return len([i for i in self.issues if i.get("state") == "closed"])

    @property
    def total_comments(self) -> int:  # UC-2.3 | PLAN-4.1
        """Total comments."""
        return len(self.comments)

    @property
    def repos_contributed_to(self) -> int:  # UC-2.3 | PLAN-4.1
        """Number of unique repositories contributed to."""
        return len(self.repositories)

    def get_summary(self) -> dict[str, Any]:  # UC-2.3 | PLAN-4.1
        """
        Get summary statistics.

        Returns:
            dict: Summary statistics
        """
        return {
            "total_commits": self.total_commits,
            "total_prs_opened": self.total_prs_opened,
            "total_prs_merged": self.total_prs_merged,
            "total_prs_reviewed": self.total_prs_reviewed,
            "total_issues_opened": self.total_issues_opened,
            "total_issues_closed": self.total_issues_closed,
            "total_comments": self.total_comments,
            "repos_contributed_to": self.repos_contributed_to,
            "most_active_day": self._get_most_active_day(),
            "most_active_repo": self._get_most_active_repo(),
        }

    def _get_most_active_day(self) -> str:  # UC-2.3 | PLAN-4.1
        """Get the most active day by number of activities."""
        days: Counter[str] = Counter()

        for commit in self.commits:
            date_str = (commit.get("date") or "")[:10]
            if date_str:
                days[date_str] += 1

        for pr in self.pull_requests:
            date_str = (pr.get("created_at") or "")[:10]
            if date_str:
                days[date_str] += 1

        for issue in self.issues:
            date_str = (issue.get("created_at") or "")[:10]
            if date_str:
                days[date_str] += 1

        for review in self.reviews:
            date_str = (review.get("submitted_at") or "")[:10]
            if date_str:
                days[date_str] += 1

        for comment in self.comments:
            date_str = (comment.get("created_at") or "")[:10]
            if date_str:
                days[date_str] += 1

        if not days:
            return ""

        return days.most_common(1)[0][0]

    def _get_most_active_repo(self) -> str:  # UC-2.3 | PLAN-4.1
        """Get the most active repository."""
        repos: Counter[str] = Counter()

        for commit in self.commits:
            repo = commit.get("repository", "")
            if repo:
                repos[repo] += 1

        for pr in self.pull_requests:
            repo = pr.get("repository", "")
            if repo:
                repos[repo] += 1

        for issue in self.issues:
            repo = issue.get("repository", "")
            if repo:
                repos[repo] += 1

        if not repos:
            return ""

        return repos.most_common(1)[0][0]


class DataAggregator:  # UC-2.3, UC-7.1 | PLAN-4.1
    """Aggregate data from multiple sources into unified structure."""

    def __init__(self, username: str, start_date: date, end_date: date):
        """
        Initialize aggregator.

        Args:
            username: GitHub username
            start_date: Period start date
            end_date: Period end date
        """
        self.username = username
        self.start_date = start_date
        self.end_date = end_date

    def aggregate(
        self,
        commits: list[dict[str, Any]] | None = None,
        pull_requests: list[dict[str, Any]] | None = None,
        issues: list[dict[str, Any]] | None = None,
        reviews: list[dict[str, Any]] | None = None,
        comments: list[dict[str, Any]] | None = None,
        **kwargs  # UC-7.1 | PLAN-3.7 - Accept extra keys like 'events' without error
    ) -> AggregatedData:  # UC-2.3 | PLAN-4.1
        """
        Combine data from all sources.

        Args:
            commits: List of commit records
            pull_requests: List of PR records
            issues: List of issue records
            reviews: List of review records
            comments: List of comment records
            **kwargs: Additional data (e.g., events for metrics calculation)

        Returns:
            AggregatedData: Combined and filtered data
        """
        # Initialize with empty lists if None
        commits = commits or []
        pull_requests = pull_requests or []
        issues = issues or []
        reviews = reviews or []
        comments = comments or []

        # Filter by date range
        commits = self._filter_by_date(commits, "date")
        # Filter PRs - keep if created in period OR has activity in period
        pull_requests = self._filter_prs_by_date(pull_requests)
        issues = self._filter_by_date(issues, "created_at")
        reviews = self._filter_by_date(reviews, "submitted_at")
        comments = self._filter_by_date(comments, "created_at")

        # Collect unique repositories
        repositories = self._collect_repositories(
            commits, pull_requests, issues, reviews
        )

        return AggregatedData(
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
            reviews=reviews,
            comments=comments,
            start_date=self.start_date,
            end_date=self.end_date,
            username=self.username,
            repositories=repositories,
        )

    def _filter_by_date(
        self,
        items: list[dict[str, Any]],
        date_field: str
    ) -> list[dict[str, Any]]:  # UC-2.3 | PLAN-4.1
        """
        Filter items by date range.

        Args:
            items: List of items to filter
            date_field: Name of the date field

        Returns:
            list[dict]: Filtered items
        """
        filtered: list[dict[str, Any]] = []

        for item in items:
            date_str = self._extract_date(item, date_field)
            if date_str:
                if self.start_date.isoformat() <= date_str <= self.end_date.isoformat():
                    filtered.append(item)

        return filtered

    def _filter_prs_by_date(
        self,
        pull_requests: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.3 | PLAN-4.1
        """
        Filter PRs by date range, keeping PRs with period activity.

        Keeps PRs that either:
        - Were created in the period, OR
        - Have the has_period_activity flag (activity in period)

        Args:
            pull_requests: List of PRs to filter

        Returns:
            list[dict]: Filtered PRs
        """
        filtered: list[dict[str, Any]] = []

        for pr in pull_requests:
            # Keep if has activity in period
            if pr.get("has_period_activity"):
                filtered.append(pr)
                continue

            # Otherwise check created_at
            date_str = self._extract_date(pr, "created_at")
            if date_str:
                if self.start_date.isoformat() <= date_str <= self.end_date.isoformat():
                    filtered.append(pr)

        return filtered

    def _extract_date(
        self,
        item: dict[str, Any],
        date_field: str
    ) -> str:  # UC-2.3 | PLAN-4.1
        """
        Extract date string from item.

        Args:
            item: Item dictionary
            date_field: Name of the date field

        Returns:
            str: Date string (YYYY-MM-DD) or empty string
        """
        date_value = item.get(date_field, "")
        if date_value:
            return str(date_value)[:10]
        return ""

    def _collect_repositories(
        self,
        commits: list[dict[str, Any]],
        pull_requests: list[dict[str, Any]],
        issues: list[dict[str, Any]],
        reviews: list[dict[str, Any]],
    ) -> list[str]:  # UC-2.3 | PLAN-4.1
        """
        Collect unique repository names.

        Args:
            commits: List of commits
            pull_requests: List of PRs
            issues: List of issues
            reviews: List of reviews

        Returns:
            list[str]: Sorted list of unique repository names
        """
        repos: set[str] = set()

        for commit in commits:
            repo = commit.get("repository", "")
            if repo:
                repos.add(repo)

        for pr in pull_requests:
            repo = pr.get("repository", "")
            if repo:
                repos.add(repo)

        for issue in issues:
            repo = issue.get("repository", "")
            if repo:
                repos.add(repo)

        for review in reviews:
            repo = review.get("repository", "")
            if repo:
                repos.add(repo)

        return sorted(repos)

    def get_repo_breakdown(
        self,
        data: AggregatedData
    ) -> list[dict[str, Any]]:  # UC-2.3 | PLAN-4.1
        """
        Get activity breakdown by repository.

        Args:
            data: Aggregated data

        Returns:
            list[dict]: Activity per repository
        """
        repo_stats: dict[str, dict[str, int]] = {}

        # Initialize stats for all repos
        for repo in data.repositories:
            repo_stats[repo] = {
                "commits": 0,
                "prs": 0,
                "issues": 0,
                "reviews": 0,
            }

        # Count commits
        for commit in data.commits:
            repo = commit.get("repository", "")
            if repo and repo in repo_stats:
                repo_stats[repo]["commits"] += 1

        # Count PRs
        for pr in data.pull_requests:
            repo = pr.get("repository", "")
            if repo and repo in repo_stats:
                repo_stats[repo]["prs"] += 1

        # Count issues
        for issue in data.issues:
            repo = issue.get("repository", "")
            if repo and repo in repo_stats:
                repo_stats[repo]["issues"] += 1

        # Count reviews
        for review in data.reviews:
            repo = review.get("repository", "")
            if repo and repo in repo_stats:
                repo_stats[repo]["reviews"] += 1

        return [
            {"name": name, **stats}
            for name, stats in sorted(repo_stats.items())
        ]
