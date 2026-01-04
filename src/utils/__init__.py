# =============================================================================
# FILE: src/utils/__init__.py
# TASKS: UC-2.1, UC-2.2, UC-2.4, UC-5.1, UC-9.1, UC-10.1, UC-11.1, UC-8.1
# PLAN: Section 3, 4, 3.8, 3.9, 3.10
# =============================================================================
"""
Utility Functions Package.

This package provides common utilities used across the project:
- gh_client.py: GitHubClient wrapper for gh CLI commands
- file_utils.py: File operations (report naming, writing)
- date_utils.py: Date range calculations and formatting
- cache.py: Request/response caching with TTL
- logger.py: Structured logging with Rich formatting (UC-9.1)
- log_cleanup.py: Log file rotation and cleanup (UC-10.1)
- report_cleanup.py: Report archival and cleanup (UC-11.1)
- repo_filter.py: Repository filtering utilities (UC-5.1)

All utilities follow the configuration settings from config.yaml.

Usage:
    from src.utils import GitHubClient, get_period_range
    from src.utils import ResponseCache, create_cache
    from src.utils import filter_repositories, filter_items_by_repo
    from src.utils import setup_logger, Logger
    from src.utils import LogCleaner, cleanup_logs
    from src.utils import ReportCleaner, cleanup_reports
"""
# UC-2.1, UC-2.2, UC-2.4, UC-5.1, UC-9.1, UC-10.1, UC-11.1, UC-8.1

from .gh_client import GitHubClient, GitHubClientError
from .date_utils import (
    get_period_range,
    get_period_dates_str,
    get_week_ranges,
    get_current_month,
    get_current_quarter,
    get_current_year,
    parse_period,
    format_period,
    is_within_range,
    parse_iso_datetime,
    parse_iso_date,
)
from .file_utils import (
    ensure_dir,
    get_next_version,
    get_next_filename,
    safe_write,
    write_report,
    read_json_file,
    list_reports,
)
from .cache import ResponseCache, create_cache
from .repo_filter import (  # UC-5.1 | PLAN-3.3
    filter_repositories,
    filter_items_by_repo,
    extract_repo_from_url,
    parse_repo_list,
)
from .logger import (  # UC-9.1 | PLAN-3.8
    Logger,
    setup_logger,
    TRACE,
)
from .log_cleanup import (  # UC-10.1 | PLAN-3.9
    LogCleaner,
    cleanup_logs,
)
from .report_cleanup import (  # UC-11.1 | PLAN-3.10
    ReportCleaner,
    cleanup_reports,
)

__all__ = [
    # GitHub client
    "GitHubClient",
    "GitHubClientError",
    # Date utilities
    "get_period_range",
    "get_period_dates_str",
    "get_week_ranges",
    "get_current_month",
    "get_current_quarter",
    "get_current_year",
    "parse_period",
    "format_period",
    "is_within_range",
    "parse_iso_datetime",
    "parse_iso_date",
    # File utilities
    "ensure_dir",
    "get_next_version",
    "get_next_filename",
    "safe_write",
    "write_report",
    "read_json_file",
    "list_reports",
    # Cache
    "ResponseCache",
    "create_cache",
    # Repository filtering (UC-5.1)
    "filter_repositories",
    "filter_items_by_repo",
    "extract_repo_from_url",
    "parse_repo_list",
    # Logging (UC-9.1)
    "Logger",
    "setup_logger",
    "TRACE",
    # Log cleanup (UC-10.1)
    "LogCleaner",
    "cleanup_logs",
    # Report cleanup (UC-11.1)
    "ReportCleaner",
    "cleanup_reports",
]
