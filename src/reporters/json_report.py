# =============================================================================
# FILE: src/reporters/json_report.py
# TASKS: UC-2.4, UC-6.1, UC-7.1
# PLAN: Section 5.1, 3.6, 3.7
# =============================================================================
"""
JSON Report Generator.

This module generates structured JSON reports:

Report Structure:
{
    "metadata": {
        "generated_at": "ISO datetime",
        "user": {"login": "username"},
        "period": {
            "type": "monthly|quarterly",
            "year": 2024,
            "month|quarter": 12|4,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD"
        },
        "schema_version": "1.0"
    },
    "summary": {...},
    "activity": {...},
    "metrics": {...}  # Only included if metrics are enabled (UC-7.1)
}

include_links (UC-6.1 | PLAN-3.6):
- When True, includes URL links in output
- When False, omits URL fields

metrics (UC-7.1 | PLAN-3.7):
- Only includes metric categories that are enabled and calculated
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING

from ..utils.file_utils import safe_write, get_next_filename

if TYPE_CHECKING:
    from ..processors.aggregator import AggregatedData


class JsonReporter:  # UC-2.4, UC-6.1 | PLAN-5.1
    """Generate JSON reports from aggregated data."""

    SCHEMA_VERSION = "1.0"

    def __init__(
        self,
        output_dir: str = "reports",
        include_links: bool = True,
        username: str | None = None
    ):
        """
        Initialize JSON reporter.

        Args:
            output_dir: Base directory for reports
            include_links: Whether to include URL links in output (UC-6.1)
            username: GitHub username for subdirectory grouping
        """
        self.output_dir = Path(output_dir)
        self.include_links = include_links  # UC-6.1 | PLAN-3.6
        self.username = username

    def generate(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None = None,
    ) -> Path:  # UC-2.4 | PLAN-5.1
        """
        Generate JSON report and write to file.

        Args:
            data: Aggregated activity data
            year: Report year
            period_type: "monthly" or "quarterly"
            period_value: Month (1-12) or quarter (1-4)
            metrics: Optional calculated metrics (UC-7.1)

        Returns:
            Path: Path to generated report file
        """
        report = self.build_report(data, year, period_type, period_value, metrics)

        # Get output file path (use username from data if not set)
        username = self.username or data.username
        output_path = get_next_filename(
            self.output_dir,
            year,
            period_type,
            period_value,
            extension="json",
            username=username
        )

        # Write report
        safe_write(output_path, report)

        return output_path

    def build_report(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:  # UC-2.4 | PLAN-5.1
        """
        Build report dictionary without writing to file.

        Args:
            data: Aggregated activity data
            year: Report year
            period_type: "monthly" or "quarterly"
            period_value: Month (1-12) or quarter (1-4)
            metrics: Optional calculated metrics (UC-7.1)

        Returns:
            dict: Complete report structure
        """
        report: dict[str, Any] = {
            "metadata": self._build_metadata(data, year, period_type, period_value),
            "summary": data.get_summary(),
            "activity": self._build_activity(data),
        }

        # UC-7.1 | PLAN-3.7 - Only include metrics if provided (enabled metrics)
        if metrics:
            report["metrics"] = metrics

        return report

    def _build_metadata(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
    ) -> dict[str, Any]:  # UC-2.4 | PLAN-5.1
        """Build metadata section of report."""
        period: dict[str, Any] = {
            "type": period_type,
            "year": year,
            "start_date": data.start_date.isoformat() if data.start_date else "",
            "end_date": data.end_date.isoformat() if data.end_date else "",
        }

        if period_type == "monthly":
            period["month"] = period_value
        else:
            period["quarter"] = period_value

        return {
            "generated_at": datetime.now().isoformat(),
            "user": {
                "login": data.username,
            },
            "period": period,
            "schema_version": self.SCHEMA_VERSION,
        }

    def _build_activity(
        self,
        data: AggregatedData
    ) -> dict[str, Any]:  # UC-2.4 | PLAN-5.1
        """Build activity section of report."""
        activity: dict[str, Any] = {
            "commits": self._format_commits(data.commits),
            "pull_requests": self._format_pull_requests(data.pull_requests),
            "issues": self._format_issues(data.issues),
            "reviews": self._format_reviews(data.reviews),
            "comments": self._format_comments(data.comments),
            "repositories": self._format_repositories(data),
        }

        return activity

    def _format_commits(
        self,
        commits: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.4, UC-6.1 | PLAN-5.1
        """Format commits for output."""
        formatted: list[dict[str, Any]] = []

        for commit in commits:
            item: dict[str, Any] = {
                "sha": commit.get("sha", ""),
                "message": commit.get("message", ""),
                "repository": commit.get("repository", ""),
                "date": commit.get("date", ""),
            }

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links:
                item["url"] = commit.get("url", "")

            if commit.get("additions") is not None:
                item["additions"] = commit.get("additions", 0)
            if commit.get("deletions") is not None:
                item["deletions"] = commit.get("deletions", 0)

            formatted.append(item)

        return formatted

    def _format_pull_requests(
        self,
        prs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.4, UC-6.1 | PLAN-5.1
        """Format pull requests for output."""
        formatted: list[dict[str, Any]] = []

        for pr in prs:
            item: dict[str, Any] = {
                "number": pr.get("number"),
                "title": pr.get("title", ""),
                "repository": pr.get("repository", ""),
                "state": pr.get("state", ""),
                "created_at": pr.get("created_at", ""),
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
            }

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links:
                item["url"] = pr.get("url", "")

            if pr.get("commits_count") is not None:
                item["commits_count"] = pr.get("commits_count", 0)
            if pr.get("additions") is not None:
                item["additions"] = pr.get("additions", 0)
            if pr.get("deletions") is not None:
                item["deletions"] = pr.get("deletions", 0)

            formatted.append(item)

        return formatted

    def _format_issues(
        self,
        issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.4, UC-6.1 | PLAN-5.1
        """Format issues for output."""
        formatted: list[dict[str, Any]] = []

        for issue in issues:
            item: dict[str, Any] = {
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "repository": issue.get("repository", ""),
                "state": issue.get("state", ""),
                "created_at": issue.get("created_at", ""),
                "closed_at": issue.get("closed_at"),
                "labels": issue.get("labels", []),
            }

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links:
                item["url"] = issue.get("url", "")

            formatted.append(item)

        return formatted

    def _format_reviews(
        self,
        reviews: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.4 | PLAN-5.1
        """Format reviews for output."""
        formatted: list[dict[str, Any]] = []

        for review in reviews:
            formatted.append({
                "pr_number": review.get("pr_number"),
                "repository": review.get("repository", ""),
                "state": review.get("state", ""),
                "submitted_at": review.get("submitted_at", ""),
                "body_length": review.get("body_length", 0),
            })

        return formatted

    def _format_comments(
        self,
        comments: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.4, UC-6.1 | PLAN-5.1
        """Format comments for output."""
        formatted: list[dict[str, Any]] = []

        for comment in comments:
            item: dict[str, Any] = {
                "type": comment.get("type", ""),
                "repository": comment.get("repository", ""),
                "issue_number": comment.get("issue_number"),
                "created_at": comment.get("created_at", ""),
                "body_length": comment.get("body_length", 0),
            }

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links:
                item["url"] = comment.get("url", "")

            formatted.append(item)

        return formatted

    def _format_repositories(
        self,
        data: AggregatedData
    ) -> list[dict[str, Any]]:  # UC-2.4 | PLAN-5.1
        """Format repository breakdown for output."""
        from ..processors.aggregator import DataAggregator

        aggregator = DataAggregator(
            data.username,
            data.start_date,
            data.end_date
        )
        return aggregator.get_repo_breakdown(data)
