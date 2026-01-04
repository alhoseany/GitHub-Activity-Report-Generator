# =============================================================================
# FILE: src/reporters/markdown_report.py
# TASKS: UC-2.4, UC-6.1, UC-7.1
# PLAN: Section 5.2, 3.6, 3.7
# =============================================================================
"""
Markdown Report Generator.

This module generates human-readable Markdown reports:

Report Sections:
# GitHub Activity Report: YYYY-MM

**User:** username
**Period:** YYYY-MM-DD to YYYY-MM-DD
**Generated:** ISO datetime

## Summary
- **Commits:** N
- **PRs Opened:** N
...

## Commits
...

## Pull Requests
...

## Issues
...

Commit Message Format (UC-6.1 | PLAN-3.6):
- full: Complete message
- first_line: First line only
- truncated: First 100 characters

Metrics Sections (UC-7.1 | PLAN-3.7):
- Only included if respective metric is enabled in config
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING

from ..utils.file_utils import safe_write, get_next_filename
from ..utils.date_utils import format_period

if TYPE_CHECKING:
    from ..processors.aggregator import AggregatedData


class MarkdownReporter:  # UC-2.4, UC-6.1 | PLAN-5.2
    """Generate Markdown reports from aggregated data."""

    def __init__(
        self,
        output_dir: str = "reports",
        include_links: bool = True,
        commit_message_format: Literal["full", "first_line", "truncated"] = "truncated",
        username: str | None = None
    ):
        """
        Initialize Markdown reporter.

        Args:
            output_dir: Base directory for reports
            include_links: Whether to include URL links in output (UC-6.1)
            commit_message_format: How to format commit messages (UC-6.1)
                - "full": Complete message
                - "first_line": First line only
                - "truncated": First 100 characters
            username: GitHub username for subdirectory grouping
        """
        self.output_dir = Path(output_dir)
        self.include_links = include_links  # UC-6.1 | PLAN-3.6
        self.commit_message_format = commit_message_format  # UC-6.1 | PLAN-3.6
        self.username = username

    def generate(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None = None,
    ) -> Path:  # UC-2.4 | PLAN-5.2
        """
        Generate Markdown report and write to file.

        Args:
            data: Aggregated activity data
            year: Report year
            period_type: "monthly" or "quarterly"
            period_value: Month (1-12) or quarter (1-4)
            metrics: Optional calculated metrics (UC-7.1)

        Returns:
            Path: Path to generated report file
        """
        content = self.build_report(data, year, period_type, period_value, metrics)

        # Get output file path (use username from data if not set)
        username = self.username or data.username
        output_path = get_next_filename(
            self.output_dir,
            year,
            period_type,
            period_value,
            extension="md",
            username=username
        )

        # Write report
        safe_write(output_path, content)

        return output_path

    def build_report(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None = None,
    ) -> str:  # UC-2.4 | PLAN-5.2
        """
        Build Markdown report content.

        Args:
            data: Aggregated activity data
            year: Report year
            period_type: "monthly" or "quarterly"
            period_value: Month (1-12) or quarter (1-4)
            metrics: Optional calculated metrics (UC-7.1)

        Returns:
            str: Markdown content
        """
        lines: list[str] = []

        # Title
        period_str = format_period(year, period_type, period_value)
        lines.append(f"# GitHub Activity Report: {period_str}")
        lines.append("")

        # Metadata
        lines.append(f"**User:** {data.username}")
        start_str = data.start_date.isoformat() if data.start_date else "N/A"
        end_str = data.end_date.isoformat() if data.end_date else "N/A"
        lines.append(f"**Period:** {start_str} to {end_str}")
        lines.append(f"**Generated:** {datetime.now().isoformat()}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        summary = data.get_summary()
        lines.append(f"- **Commits:** {summary['total_commits']}")
        lines.append(f"- **PRs Opened:** {summary['total_prs_opened']}")
        lines.append(f"- **PRs Merged:** {summary['total_prs_merged']}")
        lines.append(f"- **PRs Reviewed:** {summary['total_prs_reviewed']}")
        lines.append(f"- **Issues Opened:** {summary['total_issues_opened']}")
        lines.append(f"- **Issues Closed:** {summary['total_issues_closed']}")
        lines.append(f"- **Comments:** {summary['total_comments']}")
        lines.append(f"- **Repos Contributed:** {summary['repos_contributed_to']}")
        lines.append("")

        # Commits
        if data.commits:
            lines.extend(self._format_commits_section(data.commits))
            lines.append("")

        # Pull Requests
        if data.pull_requests:
            lines.extend(self._format_prs_section(data.pull_requests))
            lines.append("")

        # Issues
        if data.issues:
            lines.extend(self._format_issues_section(data.issues))
            lines.append("")

        # Reviews
        if data.reviews:
            lines.extend(self._format_reviews_section(data.reviews))
            lines.append("")

        # Metrics (if provided)  # UC-7.1 | PLAN-3.7
        if metrics:
            lines.extend(self._format_metrics_section(metrics))
            lines.append("")

        # Notes section - explain metrics
        if metrics:
            lines.extend(self._format_notes_section(metrics))

        return "\n".join(lines)

    def _format_commit_message(self, message: str) -> str:  # UC-6.1 | PLAN-3.6
        """
        Format commit message based on configuration.

        Args:
            message: Raw commit message

        Returns:
            Formatted message according to commit_message_format setting:
            - "full": Complete message
            - "first_line": First line only
            - "truncated": First 100 characters
        """
        if not message:
            return ""

        if self.commit_message_format == "full":
            # Return complete message
            return message
        elif self.commit_message_format == "first_line":
            # Return first line only
            return message.split("\n")[0]
        else:  # truncated - first 100 characters  # UC-6.1 | PLAN-3.6
            first_line = message.split("\n")[0]
            if len(first_line) > 100:
                return first_line[:97] + "..."
            return first_line

    def _format_commits_section(
        self,
        commits: list[dict[str, Any]]
    ) -> list[str]:  # UC-2.4, UC-6.1 | PLAN-5.2
        """Format commits section."""
        lines: list[str] = ["## Commits", ""]

        # Group by repository
        by_repo: dict[str, list[dict[str, Any]]] = {}
        for commit in commits:
            repo = commit.get("repository", "Unknown")
            by_repo.setdefault(repo, []).append(commit)

        for repo, repo_commits in sorted(by_repo.items()):
            lines.append(f"### {repo}")
            lines.append("")

            for commit in repo_commits:
                sha = commit.get("sha", "")[:7]
                message = self._format_commit_message(commit.get("message", ""))
                date_str = (commit.get("date") or "")[:10]

                # UC-6.1 | PLAN-3.6 - respect include_links setting
                if self.include_links and commit.get("url"):
                    lines.append(f"- [`{sha}`]({commit['url']}) {message} ({date_str})")
                else:
                    lines.append(f"- `{sha}` {message} ({date_str})")

            lines.append("")

        return lines

    def _format_prs_section(
        self,
        prs: list[dict[str, Any]]
    ) -> list[str]:  # UC-2.4, UC-6.1 | PLAN-5.2
        """Format pull requests section."""
        lines: list[str] = ["## Pull Requests", ""]

        for pr in prs:
            number = pr.get("number", "")
            title = pr.get("title", "")
            state = pr.get("state", "").upper()
            repo = pr.get("repository", "")

            # Determine state emoji/indicator
            if pr.get("merged_at"):
                state_indicator = "[MERGED]"
            elif state == "CLOSED":
                state_indicator = "[CLOSED]"
            else:
                state_indicator = "[OPEN]"

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links and pr.get("url"):
                lines.append(f"- {state_indicator} [{repo}#{number}]({pr['url']}) {title}")
            else:
                lines.append(f"- {state_indicator} {repo}#{number} {title}")

        return lines

    def _format_issues_section(
        self,
        issues: list[dict[str, Any]]
    ) -> list[str]:  # UC-2.4, UC-6.1 | PLAN-5.2
        """Format issues section."""
        lines: list[str] = ["## Issues", ""]

        for issue in issues:
            number = issue.get("number", "")
            title = issue.get("title", "")
            state = issue.get("state", "").upper()
            repo = issue.get("repository", "")
            labels = issue.get("labels", [])

            state_indicator = f"[{state}]" if state else ""
            labels_str = f" ({', '.join(labels)})" if labels else ""

            # UC-6.1 | PLAN-3.6 - respect include_links setting
            if self.include_links and issue.get("url"):
                lines.append(f"- {state_indicator} [{repo}#{number}]({issue['url']}) {title}{labels_str}")
            else:
                lines.append(f"- {state_indicator} {repo}#{number} {title}{labels_str}")

        return lines

    def _format_reviews_section(
        self,
        reviews: list[dict[str, Any]]
    ) -> list[str]:  # UC-2.4 | PLAN-5.2
        """Format reviews section."""
        lines: list[str] = ["## Reviews", ""]

        # Group by state
        by_state: dict[str, list[dict[str, Any]]] = {}
        for review in reviews:
            state = review.get("state", "UNKNOWN")
            by_state.setdefault(state, []).append(review)

        for state, state_reviews in sorted(by_state.items()):
            lines.append(f"### {state}")
            lines.append("")

            for review in state_reviews:
                repo = review.get("repository", "")
                pr_num = review.get("pr_number", "")
                date_str = (review.get("submitted_at") or "")[:10]

                lines.append(f"- {repo}#{pr_num} ({date_str})")

            lines.append("")

        return lines

    def _format_metrics_section(
        self,
        metrics: dict[str, Any]
    ) -> list[str]:  # UC-7.1 | PLAN-3.7
        """
        Format metrics section.

        Only includes metric categories that are present in the metrics dict.
        This respects the MetricsConfig flags - if a metric type is disabled,
        it won't be in the metrics dict and won't be included in output.
        """
        lines: list[str] = ["## Metrics", ""]

        # PR Metrics - only if present  # UC-7.1 | PLAN-3.7
        if "pr_metrics" in metrics:
            pr_metrics = metrics["pr_metrics"]
            lines.append("### Pull Request Metrics")
            lines.append("")
            if "avg_time_to_merge_hours" in pr_metrics:
                lines.append(f"- **Avg Time to Merge:** {pr_metrics['avg_time_to_merge_hours']:.1f} hours")
            if "avg_commits_per_pr" in pr_metrics:
                lines.append(f"- **Avg Commits per PR:** {pr_metrics['avg_commits_per_pr']:.1f}")
            if "avg_time_to_first_review_hours" in pr_metrics:
                lines.append(f"- **Avg Time to First Review:** {pr_metrics['avg_time_to_first_review_hours']:.1f} hours")
            if "prs_merged_without_changes" in pr_metrics:
                lines.append(f"- **PRs Merged Without Changes:** {pr_metrics['prs_merged_without_changes']}")
            if "prs_with_requested_changes" in pr_metrics:
                lines.append(f"- **PRs With Requested Changes:** {pr_metrics['prs_with_requested_changes']}")
            lines.append("")

        # Review Metrics - only if present  # UC-7.1 | PLAN-3.7
        if "review_metrics" in metrics:
            review_metrics = metrics["review_metrics"]
            lines.append("### Review Metrics")
            lines.append("")
            if "approvals" in review_metrics:
                lines.append(f"- **Approvals:** {review_metrics['approvals']}")
            if "changes_requested" in review_metrics:
                lines.append(f"- **Changes Requested:** {review_metrics['changes_requested']}")
            if "reviews_with_comments" in review_metrics:
                lines.append(f"- **Reviews With Comments:** {review_metrics['reviews_with_comments']}")
            if "avg_review_turnaround_hours" in review_metrics:
                lines.append(f"- **Avg Review Turnaround:** {review_metrics['avg_review_turnaround_hours']:.1f} hours")
            lines.append("")

        # Engagement Metrics - only if present  # UC-7.1 | PLAN-3.7
        if "engagement_metrics" in metrics:
            engagement = metrics["engagement_metrics"]
            lines.append("### Engagement Metrics")
            lines.append("")
            if "avg_response_time_hours" in engagement:
                lines.append(f"- **Avg Response Time:** {engagement['avg_response_time_hours']:.1f} hours")
            if "comment_to_code_ratio" in engagement:
                lines.append(f"- **Comment to Code Ratio:** {engagement['comment_to_code_ratio']:.2f}")
            if "collaboration_score" in engagement:
                lines.append(f"- **Collaboration Score:** {engagement['collaboration_score']:.1f}")
            lines.append("")

        # Productivity Patterns - only if present  # UC-7.1 | PLAN-3.7
        if "productivity_by_day" in metrics:
            lines.append("### Productivity by Day")
            lines.append("")
            for day, count in metrics["productivity_by_day"].items():
                if count > 0:
                    lines.append(f"- **{day}:** {count}")
            lines.append("")

        if "productivity_by_hour" in metrics:
            lines.append("### Productivity by Hour")
            lines.append("")
            # Show only hours with activity
            active_hours = [(h, c) for h, c in metrics["productivity_by_hour"].items() if c > 0]
            for hour, count in sorted(active_hours, key=lambda x: int(x[0])):
                lines.append(f"- **{int(hour):02d}:00:** {count}")
            lines.append("")

        # Reaction Breakdown - only if present  # UC-7.1 | PLAN-3.7
        if "reaction_breakdown" in metrics:
            breakdown = metrics["reaction_breakdown"]
            lines.append("### Reaction Breakdown")
            lines.append("")
            lines.append(f"- **Total Reactions:** {breakdown.get('total', 0)}")
            if "counts" in breakdown and breakdown["counts"]:
                for emoji, count in sorted(breakdown["counts"].items(), key=lambda x: -x[1]):
                    lines.append(f"- **{emoji}:** {count}")
            lines.append("")

        return lines

    def _format_notes_section(
        self,
        metrics: dict[str, Any]
    ) -> list[str]:
        """
        Format notes section explaining metrics calculations.

        Args:
            metrics: Calculated metrics dictionary

        Returns:
            list[str]: Lines for notes section
        """
        lines: list[str] = []

        # Only add notes if we have engagement metrics with collaboration score
        engagement = metrics.get("engagement_metrics", {})
        if not engagement or "collaboration_score" not in engagement:
            return lines

        lines.append("---")
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append("### Collaboration Score")
        lines.append("")
        lines.append("The Collaboration Score measures overall engagement using a weighted formula:")
        lines.append("")
        lines.append("```")
        lines.append("Score = (Reviews × 3) + (Comments × 1) + (Reactions × 0.5)")
        lines.append("```")
        lines.append("")
        lines.append("- **Reviews** are weighted highest (3×) as they require the most effort")
        lines.append("- **Comments** have standard weight (1×) for discussion participation")
        lines.append("- **Reactions** have low weight (0.5×) for lightweight engagement")
        lines.append("")
        lines.append("*Note: Review count includes all review actions (approvals, change requests, comments), not just unique PRs reviewed.*")
        lines.append("")

        return lines
