# =============================================================================
# FILE: src/config/settings.py
# TASKS: UC-3.1, UC-4.1, UC-5.1, UC-6.1, UC-7.1, UC-8.1, UC-9.1, UC-10.1, UC-11.1, UC-2.1, UC-2.2, UC-2.3, UC-2.4, UC-2.5
# PLAN: Sections 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
# =============================================================================
"""
Configuration Settings Dataclasses.

This module defines dataclasses for all configuration sections:
- PeriodConfig: Period type settings (UC-3.1)
- UserConfig: User and organization settings (UC-4.1)
- RepositoryConfig: Repository filter settings (UC-5.1)
- OutputConfig: Output format settings (UC-6.1)
- MetricsConfig: Metrics calculation settings (UC-7.1)
- CacheConfig: Caching settings (UC-8.1)
- FetchingConfig: Fetching strategy settings
- LoggingConfig: Logging settings (UC-9.1)
- LogCleanupConfig: Log cleanup settings (UC-10.1)
- ReportCleanupConfig: Report cleanup settings (UC-11.1)
- Settings: Master settings container
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Any, TYPE_CHECKING


@dataclass
class PeriodConfig:  # UC-3.1 | PLAN-3.1
    """Period configuration settings."""
    default_type: Literal["monthly", "quarterly"] = "monthly"


@dataclass
class UserConfig:  # UC-4.1 | PLAN-3.2
    """
    User configuration settings.

    Attributes:
        username: GitHub username. Can be set via:
            - CLI: --user/-u
            - Environment: GITHUB_ACTIVITY_USER
            - Config: user.username
            - Default: auto-detect from gh CLI
        organizations: List of organizations to filter by.
            Empty list means all organizations.
    """
    username: str | None = None  # None or "" = auto-detect from gh CLI
    organizations: list[str] = field(default_factory=list)  # empty = all orgs


@dataclass
class RepositoryConfig:  # UC-5.1 | PLAN-3.3
    """
    Repository filter configuration.

    Attributes:
        include_private: Include private repositories (default: True)
        include_forks: Include forked repositories (default: False)
        include: Whitelist of repos to include. Empty list = all repos.
            Format: ["owner/repo1", "owner/repo2"]
        exclude: Blacklist of repos to exclude.
            Format: ["owner/repo-to-skip"]
    """
    include_private: bool = True
    include_forks: bool = False
    include: list[str] = field(default_factory=list)  # UC-5.1 | PLAN-3.3 - whitelist
    exclude: list[str] = field(default_factory=list)  # UC-5.1 | PLAN-3.3 - blacklist

    def should_include(self, repo: dict[str, Any]) -> bool:  # UC-5.1 | PLAN-3.3
        """
        Check if a repository should be included based on filters.

        Filter priority:
        1. Check whitelist (if not empty, repo must match a pattern)
        2. Check blacklist (if matches blacklist pattern, exclude)
        3. Check private filter
        4. Check fork filter

        Supports patterns:
        - Exact match: "owner/repo"
        - Wildcard patterns: "owner/*" (all repos by owner)

        Args:
            repo: Repository dictionary with keys like:
                - full_name: "owner/repo"
                - private: bool
                - fork: bool

        Returns:
            bool: True if repository should be included
        """
        import fnmatch

        full_name = repo.get("full_name", "")

        # Check whitelist (if not empty) - supports wildcards
        if self.include:
            matches_any = any(
                fnmatch.fnmatch(full_name, pattern) for pattern in self.include
            )
            if not matches_any:
                return False

        # Check blacklist - supports wildcards
        if self.exclude:
            matches_exclude = any(
                fnmatch.fnmatch(full_name, pattern) for pattern in self.exclude
            )
            if matches_exclude:
                return False

        # Check private filter
        if repo.get("private", False) and not self.include_private:
            return False

        # Check fork filter
        if repo.get("fork", False) and not self.include_forks:
            return False

        return True


@dataclass
class FetchingConfig:  # UC-2.2 | PLAN-3.4
    """Fetching strategy configuration."""
    high_activity_threshold: int = 100
    request_delay: float = 1.0
    max_retries: int = 3
    backoff_base: float = 2.0
    timeout: int = 30


@dataclass
class CacheConfig:  # UC-8.1 | PLAN-3.5
    """
    Caching configuration.

    Attributes:
        enabled: Whether caching is enabled (default: True)
        directory: Cache directory path (default: ".cache")
        ttl_hours: Time-to-live in hours (default: 24)
    """
    enabled: bool = True
    directory: str = ".cache"
    ttl_hours: int = 24

    @property
    def ttl_seconds(self) -> int:  # UC-8.1 | PLAN-3.5
        """Get TTL in seconds."""
        return self.ttl_hours * 3600


@dataclass
class OutputConfig:  # UC-6.1 | PLAN-3.6
    """
    Output configuration.

    Attributes:
        directory: Output directory for reports (default: "reports")
        formats: List of output formats (default: ["json", "markdown"])
        include_links: Whether to include URL links in output (default: True)
        commit_message_format: How to format commit messages:
            - "full": Complete message
            - "first_line": First line only
            - "truncated": First 100 characters
    """
    directory: str = "reports"
    formats: list[str] = field(default_factory=lambda: ["json", "markdown"])
    include_links: bool = True
    commit_message_format: Literal["full", "first_line", "truncated"] = "truncated"


@dataclass
class MetricsConfig:  # UC-7.1 | PLAN-3.7
    """
    Metrics calculation configuration.

    All metrics are enabled by default. Disable individual metrics
    to speed up report generation.

    Attributes:
        pr_metrics: Calculate PR metrics (avg commits/PR, merge time, etc.)
        review_metrics: Calculate review metrics (turnaround time, approvals, etc.)
        engagement_metrics: Calculate engagement metrics (response time, collaboration)
        productivity_patterns: Calculate activity patterns by day/hour
        reaction_breakdown: Calculate reaction emoji breakdown
    """
    pr_metrics: bool = True
    review_metrics: bool = True
    engagement_metrics: bool = True
    productivity_patterns: bool = True
    reaction_breakdown: bool = True


# =============================================================================
# Logging Configuration (UC-9.1 | PLAN-3.8)
# =============================================================================

@dataclass
class LogPerformanceConfig:  # UC-9.1 | PLAN-3.8
    """Performance logging configuration."""
    log_api_calls: bool = True
    log_timing: bool = True
    log_memory: bool = False
    slow_threshold_ms: int = 1000


# =============================================================================
# Log Cleanup Configuration (UC-10.1 | PLAN-3.9)
# =============================================================================

@dataclass
class ErrorLogCleanupConfig:  # UC-10.1 | PLAN-3.9
    """
    Error log rotation configuration.

    Attributes:
        max_size_mb: Rotate error log when size exceeds (default: 10)
        max_files: Keep max N rotated error log files (default: 10)
        max_age_days: Delete error logs older than N days (default: 90)
        compress_rotated: Compress rotated error logs (default: False)
    """
    max_size_mb: int = 10
    max_files: int = 10
    max_age_days: int = 90
    compress_rotated: bool = False


@dataclass
class LogCleanupConfig:  # UC-10.1 | PLAN-3.9
    """
    Log cleanup configuration.

    Attributes:
        trigger: When to run cleanup - startup/shutdown/both/manual (default: "startup")
        retention_days: Delete logs older than N days (default: 30)
        max_size_mb: Max total size of all logs in MB (default: 100)
        max_files: Max number of log files (default: 50)
        strategy: Cleanup strategy - age/size/count (default: "age")
    """
    trigger: Literal["startup", "shutdown", "both", "manual"] = "startup"
    retention_days: int = 30
    max_size_mb: int = 100
    max_files: int = 50
    strategy: Literal["age", "size", "count", "oldest_first"] = "age"
    # Additional fields for compatibility with more detailed config
    retention_days_performance: int = 14
    max_total_size_mb: int = 500
    max_file_size_mb: int = 50
    keep_minimum_days: int = 7
    error_log: ErrorLogCleanupConfig = field(default_factory=ErrorLogCleanupConfig)


@dataclass
class LogFileConfig:  # UC-9.1 | PLAN-3.8
    """
    Log file configuration.

    Attributes:
        enabled: Enable file logging (default: True)
        directory: Log directory path (default: "logs")
        timestamp_format: Format for timestamps in filenames
        format: Log format - "%(asctime)s - %(levelname)s - %(message)s"
        separate_errors: Log errors to separate file (default: True)
        cleanup: Log cleanup configuration
    """
    enabled: bool = True
    directory: str = "logs"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    format: str = "%(asctime)s - %(levelname)s - %(message)s"
    separate_errors: bool = True
    # Additional fields for compatibility
    organize_by_date: bool = True
    error_file: str = "errors.log"
    performance_log: bool = True
    cleanup: LogCleanupConfig = field(default_factory=LogCleanupConfig)


@dataclass
class LoggingConfig:  # UC-9.1 | PLAN-3.8
    """
    Complete logging configuration.

    Attributes:
        level: Log level - DEBUG/INFO/WARNING/ERROR (default: "INFO")
        colorize: Enable colored console output (default: True)
        show_timestamps: Show timestamps in console output (default: True)
        progress_style: Progress bar style - "rich"/"simple"/"none" (default: "rich")
        file: LogFileConfig for file logging settings
    """
    level: str = "INFO"
    colorize: bool = True
    show_timestamps: bool = True
    progress_style: Literal["rich", "simple", "none"] = "rich"
    file: LogFileConfig = field(default_factory=LogFileConfig)
    performance: LogPerformanceConfig = field(default_factory=LogPerformanceConfig)


# =============================================================================
# Report Cleanup Configuration (UC-11.1 | PLAN-3.10)
# =============================================================================

@dataclass
class ReportCleanupConfig:  # UC-11.1 | PLAN-3.10
    """
    Report cleanup configuration.

    Attributes:
        enabled: Enable automatic cleanup (default: True)
        keep_versions: Keep N versions per period (default: 3)
        retention_days: Delete reports older than N days (default: 90)
        trigger: When to run cleanup - startup/shutdown/both/manual (default: "shutdown")
    """
    enabled: bool = True
    keep_versions: int = 3
    retention_days: int = 90
    trigger: Literal["startup", "shutdown", "both", "manual"] = "shutdown"
    # Additional fields for compatibility
    retention_years: int = 2
    max_total_size_mb: int = 1000
    max_file_size_mb: int = 100
    max_reports: int = 500
    keep_minimum_months: int = 6
    strategy: Literal["oldest_first", "largest_first"] = "oldest_first"
    archive: "ArchiveConfig" = field(default_factory=lambda: ArchiveConfig())


@dataclass
class ArchiveConfig:  # UC-11.1 | PLAN-3.10
    """Archive configuration."""
    enabled: bool = True
    directory: str = "reports/archive"
    compress: bool = True
    archive_after_days: int = 365


# =============================================================================
# Master Settings Container
# =============================================================================

@dataclass
class Settings:  # UC-2.5 | PLAN-3
    """Master settings container combining all configuration sections."""
    period: PeriodConfig = field(default_factory=PeriodConfig)
    user: UserConfig = field(default_factory=UserConfig)
    repositories: RepositoryConfig = field(default_factory=RepositoryConfig)
    fetching: FetchingConfig = field(default_factory=FetchingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)  # UC-8.1 | PLAN-3.5
    output: OutputConfig = field(default_factory=OutputConfig)  # UC-6.1 | PLAN-3.6
    metrics: MetricsConfig = field(default_factory=MetricsConfig)  # UC-7.1 | PLAN-3.7
    logging: LoggingConfig = field(default_factory=LoggingConfig)  # UC-9.1 | PLAN-3.8
    output_cleanup: ReportCleanupConfig = field(default_factory=ReportCleanupConfig)  # UC-11.1 | PLAN-3.10
