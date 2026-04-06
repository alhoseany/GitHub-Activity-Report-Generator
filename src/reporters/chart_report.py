# =============================================================================
# FILE: src/reporters/chart_report.py
# TASKS: UC-6.1
# PLAN: Section 5.3
# =============================================================================
"""
Chart Report Generator.

Generates a visual dashboard PNG with matplotlib charts showing:
- Activity by repository
- Productivity by day of week
- Productivity by hour
- Review breakdown
- Release contributions
- Activity summary stats
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (no GUI needed)
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from ..utils.file_utils import ensure_dir, get_next_filename

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..processors.aggregator import AggregatedData

logger = logging.getLogger(__name__)

# Professional color palette
COLORS = {
    'primary': '#2563eb',      # blue
    'secondary': '#059669',    # green
    'accent': '#d97706',       # amber
    'danger': '#dc2626',       # red
    'light': '#93c5fd',        # light blue
    'bg': '#f8fafc',           # slate-50
    'text': '#1e293b',         # slate-800
}

# Ordered days of the week
DAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


class ChartReporter:  # UC-6.1 | PLAN-5.3
    """Generate visual chart dashboard from report data."""

    def __init__(
        self,
        output_dir: str = "reports",
        username: str = "",
    ):
        """
        Initialize chart reporter.

        Args:
            output_dir: Base directory for reports.
            username: GitHub username for subdirectory grouping.
        """
        self.output_dir = Path(output_dir)
        self.username = username

    def generate(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None = None,
    ) -> Path:  # UC-6.1 | PLAN-5.3
        """
        Generate chart dashboard PNG.

        Args:
            data: Aggregated activity data.
            year: Report year.
            period_type: "monthly" or "quarterly".
            period_value: Month (1-12) or quarter (1-4).
            metrics: Optional calculated metrics.

        Returns:
            Path to saved PNG file.
        """
        username = self.username or data.username
        output_path = get_next_filename(
            self.output_dir,
            year,
            period_type,
            period_value,
            extension="png",
            username=username,
        )

        try:
            fig = self._build_dashboard(data, year, period_type, period_value, metrics)
            ensure_dir(output_path.parent)
            fig.savefig(
                str(output_path),
                dpi=150,
                bbox_inches="tight",
                facecolor=COLORS['bg'],
            )
            plt.close(fig)
        except Exception:
            logger.exception("Failed to generate chart dashboard")
            raise

        return output_path

    # ------------------------------------------------------------------
    # Dashboard assembly
    # ------------------------------------------------------------------

    def _build_dashboard(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None,
    ) -> plt.Figure:
        """Build the 3x2 chart dashboard figure."""
        fig, axes = plt.subplots(
            nrows=3, ncols=2, figsize=(16, 12),
            facecolor=COLORS['bg'],
        )

        # Suptitle
        if period_type == "monthly":
            period_label = f"{year}-{period_value:02d}"
        else:
            period_label = f"{year} Q{period_value}"
        fig.suptitle(
            f"GitHub Activity Dashboard  --  {period_label}",
            fontsize=16,
            fontweight="bold",
            color=COLORS['text'],
            y=0.98,
        )

        # Row 0
        self._plot_repo_activity(axes[0, 0], data)
        self._plot_productivity_by_day(axes[0, 1], metrics)

        # Row 1
        self._plot_productivity_by_hour(axes[1, 0], metrics)
        self._plot_review_breakdown(axes[1, 1], metrics)

        # Row 2
        self._plot_release_contributions(axes[2, 0], metrics)
        self._plot_summary_stats(axes[2, 1], data, metrics)

        fig.tight_layout(rect=[0, 0, 1, 0.95])
        return fig

    # ------------------------------------------------------------------
    # Individual subplot renderers
    # ------------------------------------------------------------------

    def _plot_repo_activity(self, ax: Axes, data: AggregatedData) -> None:
        """Horizontal stacked bar chart of activity by repository."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Activity by Repository", fontsize=12, fontweight="bold",
                      color=COLORS['text'])

        # Compute per-repo counts
        repo_commits: Counter[str] = Counter()
        repo_prs: Counter[str] = Counter()
        repo_reviews: Counter[str] = Counter()

        for commit in data.commits:
            repo = commit.get("repository", "")
            if repo:
                repo_commits[repo] += 1
        for pr in data.pull_requests:
            repo = pr.get("repository", "")
            if repo:
                repo_prs[repo] += 1
        for review in data.reviews:
            repo = review.get("repository", "")
            if repo:
                repo_reviews[repo] += 1

        # Merge all repo names
        all_repos = set(repo_commits) | set(repo_prs) | set(repo_reviews)
        if not all_repos:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        # Sort by total activity descending, keep top 8
        totals = {
            r: repo_commits[r] + repo_prs[r] + repo_reviews[r]
            for r in all_repos
        }
        sorted_repos = sorted(totals, key=totals.get, reverse=True)[:8]  # type: ignore[arg-type]
        # Reverse for horizontal bars (top = highest)
        sorted_repos = list(reversed(sorted_repos))

        # Shorten labels: show only repo name if owner/repo
        labels = [r.split("/")[-1] if "/" in r else r for r in sorted_repos]
        commits_vals = [repo_commits[r] for r in sorted_repos]
        prs_vals = [repo_prs[r] for r in sorted_repos]
        reviews_vals = [repo_reviews[r] for r in sorted_repos]

        y_pos = range(len(sorted_repos))

        ax.barh(y_pos, commits_vals, color=COLORS['primary'], label="Commits")
        ax.barh(y_pos, prs_vals, left=commits_vals, color=COLORS['secondary'],
                label="PRs")
        left_for_reviews = [c + p for c, p in zip(commits_vals, prs_vals)]
        ax.barh(y_pos, reviews_vals, left=left_for_reviews, color=COLORS['accent'],
                label="Reviews")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9, color=COLORS['text'])
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.legend(fontsize=8, loc="lower right")

    def _plot_productivity_by_day(
        self, ax: Axes, metrics: dict[str, Any] | None,
    ) -> None:
        """Bar chart of activity by day of week."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Activity by Day of Week", fontsize=12, fontweight="bold",
                      color=COLORS['text'])

        prod = (metrics or {}).get("productivity_by_day")
        if not prod:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        values = [prod.get(day, 0) for day in DAY_ORDER]
        max_val = max(values) if values else 1

        # Gradient: darker bar = higher value
        bar_colors = [
            self._lerp_color(COLORS['light'], COLORS['primary'], v / max_val if max_val else 0)
            for v in values
        ]

        short_days = [d[:3] for d in DAY_ORDER]
        ax.bar(short_days, values, color=bar_colors)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.set_ylabel("Events", fontsize=9, color=COLORS['text'])

    def _plot_productivity_by_hour(
        self, ax: Axes, metrics: dict[str, Any] | None,
    ) -> None:
        """Area/line chart of activity by hour."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Activity by Hour", fontsize=12, fontweight="bold",
                      color=COLORS['text'])

        prod = (metrics or {}).get("productivity_by_hour")
        if not prod:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        hours = list(range(24))
        values = [prod.get(str(h), prod.get(h, 0)) for h in hours]

        ax.fill_between(hours, values, alpha=0.3, color=COLORS['primary'])
        ax.plot(hours, values, color=COLORS['primary'], linewidth=2)
        ax.set_xlim(0, 23)
        ax.set_xlabel("Hour", fontsize=9, color=COLORS['text'])
        ax.set_ylabel("Events", fontsize=9, color=COLORS['text'])
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(ticker.MultipleLocator(3))

    def _plot_review_breakdown(
        self, ax: Axes, metrics: dict[str, Any] | None,
    ) -> None:
        """Donut chart of review breakdown."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Review Breakdown", fontsize=12, fontweight="bold",
                      color=COLORS['text'])

        rm = (metrics or {}).get("review_metrics")
        if not rm:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        labels_vals = [
            ("Approvals", rm.get("approvals", 0), COLORS['secondary']),
            ("Changes Requested", rm.get("changes_requested", 0), COLORS['danger']),
            ("With Comments", rm.get("reviews_with_comments", 0), COLORS['primary']),
        ]

        # Filter out zero values
        labels_vals = [(l, v, c) for l, v, c in labels_vals if v > 0]
        if not labels_vals:
            ax.text(0.5, 0.5, "No review data", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        labels = [lv[0] for lv in labels_vals]
        sizes = [lv[1] for lv in labels_vals]
        colors = [lv[2] for lv in labels_vals]

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct=lambda p: f"{int(round(p * sum(sizes) / 100))}",
            startangle=90, pctdistance=0.75, textprops={"fontsize": 9},
        )
        # Draw donut hole
        centre_circle = plt.Circle((0, 0), 0.55, fc=COLORS['bg'])
        ax.add_artist(centre_circle)
        ax.set_aspect("equal")

    def _plot_release_contributions(
        self, ax: Axes, metrics: dict[str, Any] | None,
    ) -> None:
        """Horizontal bar chart of release contributions."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Release Contributions", fontsize=12, fontweight="bold",
                      color=COLORS['text'])

        rm = (metrics or {}).get("release_metrics", {})
        releases = rm.get("releases", [])

        # Filter to releases where user contributed
        contributed = [
            r for r in releases
            if r.get("contribution_weight", 0) > 0
        ]

        if not contributed:
            ax.text(0.5, 0.5, "No release data", ha="center", va="center",
                    fontsize=12, color=COLORS['text'], transform=ax.transAxes)
            ax.set_axis_off()
            return

        # Sort by weight descending, then reverse for barh layout
        contributed.sort(key=lambda r: r.get("contribution_weight", 0), reverse=True)
        contributed = list(reversed(contributed[:10]))

        labels = []
        for r in contributed:
            tag = r.get("tag_name", "")
            repo = r.get("repository", "")
            repo_short = repo.split("/")[-1] if "/" in repo else repo
            labels.append(f"{tag} ({repo_short})")

        weights = [r.get("contribution_weight", 0) for r in contributed]
        y_pos = range(len(contributed))

        ax.barh(y_pos, weights, color=COLORS['secondary'])
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8, color=COLORS['text'])
        ax.set_xlabel("Contribution Weight (%)", fontsize=9, color=COLORS['text'])
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    def _plot_summary_stats(
        self,
        ax: Axes,
        data: AggregatedData,
        metrics: dict[str, Any] | None,
    ) -> None:
        """Text panel with key activity stats."""
        ax.set_facecolor(COLORS['bg'])
        ax.set_title("Activity Summary", fontsize=12, fontweight="bold",
                      color=COLORS['text'])
        ax.set_axis_off()

        summary = data.get_summary()

        # Release stats
        total_releases = len(data.releases)
        contributed_releases = data.releases_contributed_to

        lines = [
            f"Commits:         {summary['total_commits']}",
            f"PRs Opened:      {summary['total_prs_opened']}   |   Merged: {summary['total_prs_merged']}",
            f"Reviews:         {summary['total_prs_reviewed']}",
            f"Issues:          {summary['total_issues_opened']} opened   |   {summary['total_issues_closed']} closed",
            f"Comments:        {summary['total_comments']}",
            f"Releases:        {contributed_releases}/{total_releases}",
        ]

        text_block = "\n".join(lines)
        ax.text(
            0.05, 0.5, text_block,
            fontsize=13, fontfamily="monospace",
            verticalalignment="center",
            color=COLORS['text'],
            transform=ax.transAxes,
            linespacing=1.8,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _lerp_color(color_a: str, color_b: str, t: float) -> str:
        """Linearly interpolate between two hex colors.

        Args:
            color_a: Start hex color (e.g. '#93c5fd').
            color_b: End hex color (e.g. '#2563eb').
            t: Interpolation factor 0..1.

        Returns:
            Hex color string.
        """
        t = max(0.0, min(1.0, t))

        def _hex_to_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip('#')
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        ra, ga, ba = _hex_to_rgb(color_a)
        rb, gb, bb = _hex_to_rgb(color_b)

        r = int(ra + (rb - ra) * t)
        g = int(ga + (gb - ga) * t)
        b = int(ba + (bb - ba) * t)

        return f"#{r:02x}{g:02x}{b:02x}"
