# =============================================================================
# FILE: src/orchestrator.py
# TASKS: UC-2.5, UC-3.1, UC-4.1, UC-5.1, UC-6.1, UC-7.1, UC-8.1, UC-9.1, UC-10.1, UC-11.1
# PLAN: Section 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
# =============================================================================
"""
Report Generation Orchestrator.

This module coordinates the full report generation pipeline:
1. Load configuration
2. Initialize logger (UC-9.1)
3. Run cleanup (if trigger=startup) (UC-10.1, UC-11.1)
4. Fetch data from GitHub
5. Apply repository filters (UC-5.1)
6. Aggregate data
7. Calculate metrics (UC-7.1)
8. Generate reports (UC-6.1)
9. Run cleanup (if trigger=shutdown) (UC-10.1, UC-11.1)

Period handling (UC-3.1 | PLAN-3.1):
- Monthly reports: -m/--month (1-12)
- Quarterly reports: -q/--quarter (1-4)
- Year specification: -y/--year (default: current)

User configuration (UC-4.1 | PLAN-3.2):
- CLI --user overrides all
- Environment GITHUB_ACTIVITY_USER next priority
- Config file user.username
- Auto-detect from gh CLI as fallback

Repository filtering (UC-5.1 | PLAN-3.3):
- Whitelist (include): Only include repos in list
- Blacklist (exclude): Exclude repos in list
- Private/fork filtering via config

Output settings (UC-6.1 | PLAN-3.6):
- Directory, formats, include_links, commit_message_format
- CLI options: --output-dir, --format

Metrics (UC-7.1 | PLAN-3.7):
- Calculate only enabled metric types
- Include only enabled metrics in reports

Caching (UC-8.1 | PLAN-3.5):
- Pass cache config to GitHubClient
- Respect --no-cache CLI flag

Logging (UC-9.1 | PLAN-3.8):
- Initialize structured logger
- Support colorized output with Rich
- File logging in JSONL format

Cleanup (UC-10.1, UC-11.1 | PLAN-3.9, 3.10):
- Log cleanup at startup/shutdown based on trigger config
- Report cleanup at startup/shutdown based on trigger config
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING

from .config.settings import Settings, LogCleanupConfig
from .config.loader import ConfigLoader
from .utils.gh_client import GitHubClient, GitHubClientError
from .utils.cache import ResponseCache, create_cache  # UC-8.1 | PLAN-3.5
from .utils.date_utils import get_period_range
from .utils.repo_filter import filter_items_by_repo  # UC-5.1 | PLAN-3.3
from .fetchers.events import EventsFetcher
from .fetchers.commits import CommitsFetcher
from .fetchers.pull_requests import PullRequestsFetcher
from .fetchers.issues import IssuesFetcher
from .fetchers.reviews import ReviewsFetcher
from .fetchers.comments import CommentsFetcher
from .processors.aggregator import DataAggregator, AggregatedData
from .processors.metrics import MetricsCalculator  # UC-7.1 | PLAN-3.7
from .reporters.json_report import JsonReporter
from .reporters.markdown_report import MarkdownReporter

if TYPE_CHECKING:
    from .utils.logger import Logger


class ReportOrchestrator:  # UC-2.5, UC-3.1, UC-4.1, UC-5.1, UC-6.1, UC-7.1, UC-8.1, UC-9.1, UC-10.1, UC-11.1 | PLAN-3.1
    """Orchestrate the full report generation pipeline."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        settings: Settings | None = None,
        logger: Any = None,
    ):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to config.yaml (optional)
            settings: Pre-loaded Settings object (optional)
            logger: Logger instance (optional)
        """
        self.config_path = Path(config_path) if config_path else Path("config.yaml")
        self._settings = settings
        self._logger = logger  # UC-9.1 | PLAN-3.8

        # Will be initialized during run()
        self.gh_client: GitHubClient | None = None
        self.cache: ResponseCache | None = None  # UC-8.1 | PLAN-3.5
        self.username: str = ""

    @property
    def settings(self) -> Settings:  # UC-4.1, UC-5.1 | PLAN-3.1
        """Get or load settings."""
        if self._settings is None:
            loader = ConfigLoader(self.config_path)
            self._settings = loader.load()
        return self._settings

    @property
    def logger(self) -> "Logger | None":  # UC-9.1 | PLAN-3.8
        """Get logger, initializing if needed."""
        return self._logger

    def run(
        self,
        username: str | None = None,
        period_type: Literal["monthly", "quarterly"] | None = None,
        period_value: int | None = None,
        year: int | None = None,
        output_formats: list[str] | None = None,
        output_dir: str | None = None,
        dry_run: bool = False,
        no_cache: bool = False,
    ) -> dict[str, Any]:  # UC-2.5, UC-3.1, UC-4.1, UC-6.1, UC-8.1 | PLAN-3.1
        """
        Run the full report generation pipeline.

        Args:
            username: GitHub username (or auto-detect)  # UC-4.1 | PLAN-3.2
            period_type: "monthly" or "quarterly"  # UC-3.1 | PLAN-3.1
            period_value: Month (1-12) or quarter (1-4)  # UC-3.1 | PLAN-3.1
            year: Year (default: current year)  # UC-3.1 | PLAN-3.1
            output_formats: List of formats ("json", "markdown")  # UC-6.1 | PLAN-3.6
            output_dir: Output directory override  # UC-6.1 | PLAN-3.6
            dry_run: If True, show what would be fetched without fetching
            no_cache: If True, disable caching  # UC-8.1 | PLAN-3.5

        Returns:
            dict: Result with generated file paths and summary
        """
        result: dict[str, Any] = {
            "success": False,
            "files": [],
            "summary": {},
            "errors": [],
        }

        try:
            # Step 1: Initialize logger  # UC-9.1 | PLAN-3.8
            self._initialize_logger()

            # Step 2: Initialize client and cache  # UC-4.1, UC-8.1 | PLAN-3.2, 3.5
            self._log_info("Starting report generation...")
            self._initialize(username, no_cache)

            # Step 3: Determine period  # UC-3.1 | PLAN-3.1
            period_type = period_type or self.settings.period.default_type
            if period_value is None:
                from .utils.date_utils import get_current_month, get_current_quarter
                if period_type == "monthly":
                    period_value = get_current_month()
                else:
                    period_value = get_current_quarter()

            if year is None:
                from .utils.date_utils import get_current_year
                year = get_current_year()

            start_date, end_date = get_period_range(year, period_type, period_value)
            self._log_info(f"Period: {period_type} {period_value}/{year} ({start_date} to {end_date})")

            # Step 4: Dry run check
            if dry_run:
                result["dry_run"] = True
                result["would_fetch"] = {
                    "user": self.username,
                    "period_type": period_type,
                    "period_value": period_value,
                    "year": year,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                }
                result["success"] = True
                self._log_info("Dry run - no data fetched")
                return result

            # Step 5: Run startup cleanup (if enabled)  # UC-10.1, UC-11.1 | PLAN-3.9, 3.10
            self._run_startup_cleanup()

            # Step 6: Fetch data
            self._log_info("Fetching data from GitHub...")
            fetched_data = self._fetch_all_data(start_date, end_date)

            # Step 7: Apply repository filters  # UC-5.1 | PLAN-3.3
            if self.settings.repositories.include or self.settings.repositories.exclude:
                self._log_info("Applying repository filters...")
                fetched_data = self._apply_repo_filters(fetched_data)

            # Step 8: Aggregate data
            self._log_info("Aggregating data...")
            aggregator = DataAggregator(self.username, start_date, end_date)
            aggregated = aggregator.aggregate(**fetched_data)

            # Step 9: Calculate metrics  # UC-7.1 | PLAN-3.7
            metrics: dict[str, Any] | None = None
            metrics_config = self.settings.metrics
            if self._should_calculate_metrics(metrics_config):
                self._log_info("Calculating metrics...")
                metrics = self._calculate_metrics(aggregated, fetched_data)

            # Step 10: Generate reports  # UC-6.1 | PLAN-3.6
            self._log_info("Generating reports...")
            output_formats = output_formats or self.settings.output.formats
            output_dir = output_dir or self.settings.output.directory

            files = self._generate_reports(
                aggregated,
                year,
                period_type,
                period_value,
                metrics,
                output_formats,
                output_dir,
            )
            result["files"] = [str(f) for f in files]

            # Step 11: Run shutdown cleanup (if enabled)  # UC-10.1, UC-11.1 | PLAN-3.9, 3.10
            self._run_shutdown_cleanup()

            # Set result
            result["success"] = True
            result["summary"] = aggregated.get_summary()
            self._log_info(f"Report generation complete. Files: {len(files)}")

        except GitHubClientError as e:
            error_msg = f"GitHub API error: {e}"
            result["errors"].append(error_msg)
            self._log_error(error_msg)

        except Exception as e:
            error_msg = f"Error: {e}"
            result["errors"].append(error_msg)
            self._log_error(error_msg)

        return result

    def _initialize_logger(self) -> None:  # UC-9.1 | PLAN-3.8
        """Initialize the logger if not already set."""
        if self._logger is None:
            try:
                from .utils.logger import setup_logger
                self._logger = setup_logger(
                    name="github-activity",
                    config=self.settings.logging,
                )
            except Exception:
                # Fall back to no logger if initialization fails
                pass

    def _should_calculate_metrics(self, metrics_config) -> bool:  # UC-7.1 | PLAN-3.7
        """Check if any metrics calculation is enabled."""
        return any([
            metrics_config.pr_metrics,
            metrics_config.review_metrics,
            metrics_config.engagement_metrics,
            metrics_config.productivity_patterns,
            metrics_config.reaction_breakdown,
        ])

    def _initialize(
        self,
        username: str | None,
        no_cache: bool
    ) -> None:  # UC-4.1, UC-8.1 | PLAN-3.2, 3.5
        """
        Initialize GitHub client, cache, and resolve username.

        Username resolution priority (UC-4.1 | PLAN-3.2):
        1. CLI --user argument (passed as username parameter)
        2. Environment variable GITHUB_ACTIVITY_USER (loaded into settings)
        3. Config file user.username
        4. Auto-detect from gh CLI

        Cache initialization (UC-8.1 | PLAN-3.5):
        - Respects --no-cache CLI flag
        - Uses configured directory and TTL
        """
        # UC-8.1 | PLAN-3.5 - Disable cache if --no-cache flag used
        if no_cache:
            self.settings.cache.enabled = False

        # UC-8.1 | PLAN-3.5 - Initialize cache with config settings
        self.cache = create_cache(self.settings.cache)

        # Initialize GitHub client
        self.gh_client = GitHubClient(
            request_delay=self.settings.fetching.request_delay,
            timeout=self.settings.fetching.timeout,
            cache=self.cache,  # UC-8.1 | PLAN-3.5 - pass cache to client
        )

        # Resolve username with priority: CLI > ENV > config > auto-detect
        if username:
            # CLI argument has highest priority
            self.username = username
        elif self.settings.user.username:
            # ENV or config file (ENV is applied during config loading)
            self.username = self.settings.user.username
        else:
            # Auto-detect from gh CLI as fallback
            self._log_info("Auto-detecting username from gh CLI...")
            self.username = self.gh_client.get_logged_in_user()

        self._log_info(f"Username: {self.username}")
        if self.cache and self.cache.enabled:
            self._log_info(f"Cache: enabled (TTL: {self.cache.ttl_hours}h, dir: {self.cache.config.directory})")
        else:
            self._log_info("Cache: disabled")

    def _fetch_all_data(
        self,
        start_date: date,
        end_date: date
    ) -> dict[str, list[dict[str, Any]]]:  # UC-2.5 | PLAN-3.1
        """Fetch all data types from GitHub."""
        config = self.settings.fetching

        # Initialize fetchers
        events_fetcher = EventsFetcher(self.gh_client, config, self.username, self._logger)
        commits_fetcher = CommitsFetcher(self.gh_client, config, self.username, self._logger)
        prs_fetcher = PullRequestsFetcher(self.gh_client, config, self.username, self._logger)
        issues_fetcher = IssuesFetcher(self.gh_client, config, self.username, self._logger)
        reviews_fetcher = ReviewsFetcher(self.gh_client, config, self.username, self._logger)
        comments_fetcher = CommentsFetcher(self.gh_client, config, self.username, self._logger)

        # Fetch events (limited to 90 days)
        self._log_info("Fetching events...")
        events = events_fetcher.fetch_period(start_date, end_date)
        event_comments = events_fetcher.extract_comment_events(events)

        # Fetch commits
        self._log_info("Fetching commits...")
        commits = commits_fetcher.fetch_period(start_date, end_date)

        # Fetch PRs created in period
        self._log_info("Fetching pull requests...")
        pull_requests = prs_fetcher.fetch_period(start_date, end_date)

        # Also fetch PRs updated in period (catches PRs created earlier with activity now)
        self._log_info("Fetching PRs with activity in period...")
        updated_prs = prs_fetcher.fetch_prs_updated_in_period(start_date, end_date)

        # Fetch open PRs with activity in period (GitHub's updated_at is unreliable)
        self._log_info("Checking open PRs for activity in period...")
        open_prs_with_activity = prs_fetcher.fetch_open_prs_with_activity(start_date, end_date)

        # Merge and deduplicate PRs
        seen_pr_keys: set[str] = set()
        all_prs: list[dict] = []
        for pr in pull_requests + updated_prs + open_prs_with_activity:
            pr_key = f"{pr.get('repository')}#{pr.get('number')}"
            if pr_key not in seen_pr_keys:
                seen_pr_keys.add(pr_key)
                all_prs.append(pr)
        pull_requests = all_prs

        # Enrich PRs with details (commits count, additions, deletions)
        if pull_requests:
            self._log_info("Enriching PRs with details...")
            pull_requests = prs_fetcher.enrich_with_details(pull_requests)

        # Fetch commits from unmerged PRs (not in search index)
        unmerged_prs = [pr for pr in pull_requests if pr.get("state") != "merged"]
        pr_commits: list[dict] = []
        if unmerged_prs:
            self._log_info(f"Fetching commits from {len(unmerged_prs)} unmerged PRs...")
            pr_commits = prs_fetcher.fetch_commits_from_prs(unmerged_prs, start_date, end_date)

        # Fetch reviewed PRs (for fetching reviews)
        reviewed_prs = prs_fetcher.fetch_reviewed_prs(start_date, end_date)

        # Fetch reviews for reviewed PRs
        self._log_info("Fetching reviews...")
        all_prs_for_reviews = pull_requests + reviewed_prs
        reviews = reviews_fetcher.fetch_reviews_for_prs(all_prs_for_reviews, start_date, end_date)

        # Fetch reviews ON user's authored PRs (from other reviewers)
        reviews_on_authored_prs: list[dict[str, Any]] = []
        if pull_requests:
            self._log_info("Fetching reviews on authored PRs...")
            reviews_on_authored_prs = reviews_fetcher.fetch_reviews_on_authored_prs(
                pull_requests, start_date, end_date
            )

        # Fetch issues
        self._log_info("Fetching issues...")
        issues = issues_fetcher.fetch_period(start_date, end_date)

        # Fetch comments directly via API (more complete than events)
        self._log_info("Fetching comments...")
        api_comments = comments_fetcher.fetch_period(start_date, end_date)

        # Also fetch review comments on PRs the user reviewed
        if reviewed_prs:
            self._log_info("Fetching review comments...")
            review_comments = comments_fetcher.fetch_review_comments(
                reviewed_prs, start_date, end_date
            )
            api_comments.extend(review_comments)

        # Merge comments from API with comments from events, deduplicating
        seen_comment_ids: set[str] = set()
        all_comments: list[dict] = []

        # API comments take priority (more complete data)
        for comment in api_comments:
            comment_id = str(comment.get("id", "")) or comment.get("url", "")
            if comment_id and comment_id not in seen_comment_ids:
                seen_comment_ids.add(comment_id)
                all_comments.append(comment)

        # Add event-based comments if not already seen
        for comment in event_comments:
            comment_id = str(comment.get("id", "")) or comment.get("url", "")
            if comment_id and comment_id not in seen_comment_ids:
                seen_comment_ids.add(comment_id)
                all_comments.append(comment)

        if api_comments:
            self._log_info(f"Found {len(api_comments)} comments via API, {len(event_comments)} from events")

        # Merge commits from search with commits from unmerged PRs
        seen_shas: set[str] = set()
        all_commits: list[dict] = []
        for commit in commits:
            sha = commit.get("sha", "")
            if sha not in seen_shas:
                seen_shas.add(sha)
                all_commits.append(commit)
        for commit in pr_commits:
            sha = commit.get("sha", "")
            if sha not in seen_shas:
                seen_shas.add(sha)
                all_commits.append(commit)

        if pr_commits:
            self._log_info(f"Added {len(pr_commits)} commits from unmerged PRs")

        return {
            "commits": all_commits,
            "pull_requests": pull_requests,
            "issues": issues,
            "reviews": reviews,
            "reviews_on_authored_prs": reviews_on_authored_prs,  # Reviews from others on user's PRs
            "reviewed_prs": reviewed_prs,  # PRs the user reviewed (for review turnaround)
            "comments": all_comments,  # Merged from API + events
            "events": events,  # UC-7.1 | PLAN-3.7 - needed for productivity patterns
        }

    def _apply_repo_filters(
        self,
        fetched_data: dict[str, list[dict[str, Any]]]
    ) -> dict[str, list[dict[str, Any]]]:  # UC-5.1 | PLAN-3.3
        """
        Apply repository filters to fetched data.

        Filters based on:
        - Whitelist (include): Only include repos in list
        - Blacklist (exclude): Exclude repos in list
        - Private repos: include_private setting
        - Forks: include_forks setting
        """
        repo_config = self.settings.repositories

        filtered_data: dict[str, list[dict[str, Any]]] = {}

        for data_type, items in fetched_data.items():
            original_count = len(items)
            filtered_items = filter_items_by_repo(items, repo_config)
            filtered_count = len(filtered_items)

            if original_count != filtered_count:
                self._log_info(
                    f"  {data_type}: filtered {original_count} -> {filtered_count} items"
                )

            filtered_data[data_type] = filtered_items

        return filtered_data

    def _calculate_metrics(
        self,
        data: AggregatedData,
        fetched_data: dict[str, list[dict[str, Any]]]
    ) -> dict[str, Any]:  # UC-7.1 | PLAN-3.7
        """
        Calculate metrics from aggregated data.

        Only calculates metrics that are enabled in MetricsConfig.
        Uses the MetricsCalculator class for comprehensive metrics.
        """
        metrics_config = self.settings.metrics
        calculator = MetricsCalculator(metrics_config)

        # Get events for productivity patterns
        events = fetched_data.get("events", [])

        # Get reviews on authored PRs (from other reviewers)
        reviews_on_authored_prs = fetched_data.get("reviews_on_authored_prs", [])

        # Get PRs that the user reviewed (for review turnaround calculation)
        reviewed_prs = fetched_data.get("reviewed_prs", [])

        # Use MetricsCalculator.calculate_all() which respects config flags  # UC-7.1 | PLAN-3.7
        metrics = calculator.calculate_all(
            prs=data.pull_requests,
            reviews=data.reviews,
            commits=data.commits,
            comments=data.comments,
            events=events,
            reactions=None,  # Reactions not currently fetched
            reviews_on_authored_prs=reviews_on_authored_prs,  # For PR metrics
            reviewed_prs=reviewed_prs,  # For review turnaround calc
        )

        return metrics

    def _generate_reports(
        self,
        data: AggregatedData,
        year: int,
        period_type: Literal["monthly", "quarterly"],
        period_value: int,
        metrics: dict[str, Any] | None,
        output_formats: list[str],
        output_dir: str,
    ) -> list[Path]:  # UC-2.5, UC-6.1, UC-7.1 | PLAN-3.1, 3.6
        """
        Generate reports in specified formats.

        Uses output config settings (UC-6.1):
        - include_links: Whether to include URLs in output
        - commit_message_format: How to format commit messages

        Passes metrics to reporters (UC-7.1):
        - Only enabled metrics will be included
        """
        files: list[Path] = []

        # UC-6.1 | PLAN-3.6 - Use output config settings
        include_links = self.settings.output.include_links
        commit_format = self.settings.output.commit_message_format

        if "json" in output_formats:
            reporter = JsonReporter(
                output_dir=output_dir,
                include_links=include_links,  # UC-6.1 | PLAN-3.6
            )
            # UC-7.1 | PLAN-3.7 - Metrics are conditionally included
            json_path = reporter.generate(data, year, period_type, period_value, metrics)
            files.append(json_path)
            self._log_info(f"Generated JSON: {json_path}")

        if "markdown" in output_formats:
            reporter = MarkdownReporter(
                output_dir=output_dir,
                include_links=include_links,  # UC-6.1 | PLAN-3.6
                commit_message_format=commit_format,  # UC-6.1 | PLAN-3.6
            )
            # UC-7.1 | PLAN-3.7 - Metrics are conditionally included
            md_path = reporter.generate(data, year, period_type, period_value, metrics)
            files.append(md_path)
            self._log_info(f"Generated Markdown: {md_path}")

        return files

    def _run_startup_cleanup(self) -> None:  # UC-10.1, UC-11.1 | PLAN-3.9, 3.10
        """
        Run cleanup tasks on startup if enabled.

        Checks trigger config for both log cleanup and report cleanup.
        """
        # Get cleanup configs - handle both nested and flat structures
        log_cleanup_config = self._get_log_cleanup_config()
        report_cleanup = self.settings.output_cleanup

        # UC-10.1 | PLAN-3.9 - Log cleanup at startup
        if log_cleanup_config and log_cleanup_config.trigger in ("startup", "both"):
            self._run_log_cleanup(log_cleanup_config)

        # UC-11.1 | PLAN-3.10 - Report cleanup at startup
        if report_cleanup.enabled and report_cleanup.trigger in ("startup", "both"):
            self._run_report_cleanup()

    def _run_shutdown_cleanup(self) -> None:  # UC-10.1, UC-11.1 | PLAN-3.9, 3.10
        """
        Run cleanup tasks on shutdown if enabled.

        Checks trigger config for both log cleanup and report cleanup.
        """
        # Get cleanup configs - handle both nested and flat structures
        log_cleanup_config = self._get_log_cleanup_config()
        report_cleanup = self.settings.output_cleanup

        # UC-10.1 | PLAN-3.9 - Log cleanup at shutdown
        if log_cleanup_config and log_cleanup_config.trigger in ("shutdown", "both"):
            self._run_log_cleanup(log_cleanup_config)

        # UC-11.1 | PLAN-3.10 - Report cleanup at shutdown
        if report_cleanup.enabled and report_cleanup.trigger in ("shutdown", "both"):
            self._run_report_cleanup()

    def _get_log_cleanup_config(self) -> LogCleanupConfig | None:  # UC-10.1 | PLAN-3.9
        """Get log cleanup config, handling different config structures."""
        try:
            # Try nested structure: logging.file.cleanup
            if hasattr(self.settings.logging.file, 'cleanup'):
                return self.settings.logging.file.cleanup
        except AttributeError:
            pass

        # Return default config if not found
        return LogCleanupConfig()

    def _run_log_cleanup(self, config: LogCleanupConfig) -> None:  # UC-10.1 | PLAN-3.9
        """
        Run log cleanup.

        Args:
            config: LogCleanupConfig with cleanup settings
        """
        try:
            from .utils.log_cleanup import LogCleaner

            logs_dir = Path(self.settings.logging.file.directory)
            if not logs_dir.exists():
                return

            self._log_info("Running log cleanup...")
            cleaner = LogCleaner(logs_dir, config)
            stats = cleaner.clean()

            if stats["deleted"] > 0 or stats["rotated"] > 0:
                self._log_info(
                    f"Log cleanup: deleted {stats['deleted']} files, "
                    f"rotated {stats['rotated']}, freed {stats['freed_mb']:.2f} MB"
                )
        except Exception as e:
            self._log_error(f"Log cleanup error: {e}")

    def _run_report_cleanup(self) -> None:  # UC-11.1 | PLAN-3.10
        """Run report cleanup based on config."""
        try:
            from .utils.report_cleanup import ReportCleaner

            reports_dir = Path(self.settings.output.directory)
            if not reports_dir.exists():
                return

            self._log_info("Running report cleanup...")
            cleaner = ReportCleaner(reports_dir, self.settings.output_cleanup)
            stats = cleaner.clean()

            if stats["deleted"] > 0 or stats["archived"] > 0:
                self._log_info(
                    f"Report cleanup: deleted {stats['deleted']} files, "
                    f"archived {stats['archived']}, cleaned {stats['versions_cleaned']} versions, "
                    f"freed {stats['freed_mb']:.2f} MB"
                )
        except Exception as e:
            self._log_error(f"Report cleanup error: {e}")

    def _log_info(self, message: str) -> None:  # UC-9.1 | PLAN-3.8
        """Log info message."""
        if self._logger:
            self._logger.info(message)
        else:
            print(f"[INFO] {message}", file=sys.stderr)

    def _log_error(self, message: str) -> None:  # UC-9.1 | PLAN-3.8
        """Log error message."""
        if self._logger:
            self._logger.error(message)
        else:
            print(f"[ERROR] {message}", file=sys.stderr)
