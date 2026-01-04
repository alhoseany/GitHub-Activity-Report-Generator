# =============================================================================
# FILE: src/config/loader.py
# TASKS: UC-3.1, UC-4.1, UC-5.1, UC-2.1, UC-2.5
# PLAN: Section 3.1, 3.2, 3.3
# =============================================================================
"""
Configuration Loader.

This module handles configuration loading with the following priority:
1. CLI arguments (highest priority)
2. Environment variables
3. config.yaml file
4. Default values (lowest priority)

Functions:
- load_config(): Load and merge all configuration sources
- ConfigLoader: Class for loading and managing configuration

Environment Variables (UC-4.1 | PLAN-3.2):
- GITHUB_ACTIVITY_USER: Override username
- GITHUB_ACTIVITY_OUTPUT_DIR: Override output directory
- GITHUB_ACTIVITY_LOG_LEVEL: Override log level
- GITHUB_ACTIVITY_LOG_DIR: Override log directory
- GITHUB_ACTIVITY_CACHE_DIR: Override cache directory
- GITHUB_ACTIVITY_HIGH_THRESHOLD: Override high activity threshold
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .settings import (
    Settings,
    PeriodConfig,
    UserConfig,
    RepositoryConfig,
    FetchingConfig,
    CacheConfig,
    OutputConfig,
    MetricsConfig,
    LoggingConfig,
    LogFileConfig,
    LogCleanupConfig,
    LogPerformanceConfig,
    ErrorLogCleanupConfig,
    ReportCleanupConfig,
    ArchiveConfig,
)


class ConfigLoader:  # UC-4.1, UC-5.1 | PLAN-3.2
    """Load and manage configuration from multiple sources."""

    # Environment variable mappings: ENV_VAR -> config path  # UC-4.1 | PLAN-3.2
    ENV_MAPPINGS: dict[str, tuple[str, ...]] = {
        "GITHUB_ACTIVITY_USER": ("user", "username"),
        "GITHUB_ACTIVITY_OUTPUT_DIR": ("output", "directory"),
        "GITHUB_ACTIVITY_LOG_LEVEL": ("logging", "level"),
        "GITHUB_ACTIVITY_LOG_DIR": ("logging", "file", "directory"),
        "GITHUB_ACTIVITY_CACHE_DIR": ("cache", "directory"),
        "GITHUB_ACTIVITY_HIGH_THRESHOLD": ("fetching", "high_activity_threshold"),
    }

    def __init__(self, config_path: str | Path = "config.yaml"):
        """Initialize loader with config file path."""
        self.config_path = Path(config_path)
        self._raw_config: dict[str, Any] = {}

    def load(self) -> Settings:  # UC-4.1, UC-5.1 | PLAN-3.2
        """
        Load configuration with priority:
        CLI > Environment Variables > config.yaml > Defaults

        Returns:
            Settings: Complete configuration object
        """
        # Start with empty config (defaults come from dataclasses)
        self._raw_config = {}

        # Load from YAML if exists
        if self.config_path.exists():
            self._load_yaml()

        # Apply environment variables
        self._apply_env_vars()

        # Build Settings from raw config
        return self._build_settings()

    def _load_yaml(self) -> None:  # UC-4.1 | PLAN-3.2
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    self._raw_config = loaded
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    def _apply_env_vars(self) -> None:  # UC-4.1 | PLAN-3.2
        """Apply environment variable overrides."""
        for env_var, path in self.ENV_MAPPINGS.items():
            value = os.environ.get(env_var)
            if value:
                # Convert numeric values
                if env_var == "GITHUB_ACTIVITY_HIGH_THRESHOLD":
                    value = int(value)
                self._set_nested(self._raw_config, path, value)

    def _set_nested(self, d: dict, path: tuple[str, ...], value: Any) -> None:
        """Set a nested dictionary value by path."""
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def _get_nested(self, d: dict, path: tuple[str, ...], default: Any = None) -> Any:
        """Get a nested dictionary value by path."""
        for key in path:
            if not isinstance(d, dict):
                return default
            d = d.get(key, default)
            if d is None:
                return default
        return d

    def _build_settings(self) -> Settings:  # UC-4.1, UC-5.1 | PLAN-3.2
        """Build Settings object from raw config."""
        # Build each config section
        period = self._build_period_config()
        user = self._build_user_config()
        repositories = self._build_repository_config()
        fetching = self._build_fetching_config()
        cache = self._build_cache_config()
        output = self._build_output_config()
        metrics = self._build_metrics_config()
        logging = self._build_logging_config()
        output_cleanup = self._build_report_cleanup_config()

        return Settings(
            period=period,
            user=user,
            repositories=repositories,
            fetching=fetching,
            cache=cache,
            output=output,
            metrics=metrics,
            logging=logging,
            output_cleanup=output_cleanup,
        )

    def _build_period_config(self) -> PeriodConfig:  # UC-3.1 | PLAN-3.1
        """Build PeriodConfig from raw config."""
        section = self._raw_config.get("period", {})
        return PeriodConfig(
            default_type=section.get("default_type", "monthly"),
        )

    def _build_user_config(self) -> UserConfig:  # UC-4.1 | PLAN-3.2
        """
        Build UserConfig from raw config.

        Username priority:
        1. CLI (handled at runtime)
        2. Environment variable GITHUB_ACTIVITY_USER (applied in _apply_env_vars)
        3. config.yaml user.username
        4. Auto-detect from gh CLI (when username is None or empty)
        """
        section = self._raw_config.get("user", {})
        username = section.get("username")

        # Treat empty string as None (auto-detect)
        if username == "":
            username = None

        return UserConfig(
            username=username,
            organizations=section.get("organizations", []),
        )

    def _build_repository_config(self) -> RepositoryConfig:  # UC-5.1 | PLAN-3.3
        """
        Build RepositoryConfig from raw config.

        Includes:
        - include_private: bool (default: True)
        - include_forks: bool (default: False)
        - include: list[str] - whitelist (empty = all)
        - exclude: list[str] - blacklist
        """
        section = self._raw_config.get("repositories", {})
        return RepositoryConfig(
            include_private=section.get("include_private", True),
            include_forks=section.get("include_forks", False),
            include=section.get("include", []),  # UC-5.1 | PLAN-3.3 - whitelist
            exclude=section.get("exclude", []),  # UC-5.1 | PLAN-3.3 - blacklist
        )

    def _build_fetching_config(self) -> FetchingConfig:
        """Build FetchingConfig from raw config."""
        section = self._raw_config.get("fetching", {})
        return FetchingConfig(
            high_activity_threshold=section.get("high_activity_threshold", 100),
            request_delay=section.get("request_delay", 1.0),
            max_retries=section.get("max_retries", 3),
            backoff_base=section.get("backoff_base", 2.0),
            timeout=section.get("timeout", 30),
        )

    def _build_cache_config(self) -> CacheConfig:
        """Build CacheConfig from raw config."""
        section = self._raw_config.get("cache", {})
        return CacheConfig(
            enabled=section.get("enabled", True),
            directory=section.get("directory", ".cache"),
            ttl_hours=section.get("ttl_hours", 24),
        )

    def _build_output_config(self) -> OutputConfig:
        """Build OutputConfig from raw config."""
        section = self._raw_config.get("output", {})
        return OutputConfig(
            directory=section.get("directory", "reports"),
            formats=section.get("formats", ["json", "markdown"]),
            include_links=section.get("include_links", True),
            commit_message_format=section.get("commit_message_format", "truncated"),
        )

    def _build_metrics_config(self) -> MetricsConfig:
        """Build MetricsConfig from raw config."""
        section = self._raw_config.get("metrics", {})
        return MetricsConfig(
            pr_metrics=section.get("pr_metrics", True),
            review_metrics=section.get("review_metrics", True),
            engagement_metrics=section.get("engagement_metrics", True),
            productivity_patterns=section.get("productivity_patterns", True),
            reaction_breakdown=section.get("reaction_breakdown", True),
        )

    def _build_logging_config(self) -> LoggingConfig:
        """Build LoggingConfig from raw config."""
        section = self._raw_config.get("logging", {})
        file_section = section.get("file", {})
        cleanup_section = file_section.get("cleanup", {})
        error_log_section = cleanup_section.get("error_log", {})
        perf_section = section.get("performance", {})

        error_log_cleanup = ErrorLogCleanupConfig(
            max_size_mb=error_log_section.get("max_size_mb", 10),
            max_files=error_log_section.get("max_files", 50),
            max_age_days=error_log_section.get("max_age_days", 365),
            compress_rotated=error_log_section.get("compress_rotated", True),
        )

        log_cleanup = LogCleanupConfig(
            trigger=cleanup_section.get("trigger", "startup"),
            retention_days=cleanup_section.get("retention_days", 30),
            retention_days_performance=cleanup_section.get("retention_days_performance", 14),
            max_total_size_mb=cleanup_section.get("max_total_size_mb", 500),
            max_file_size_mb=cleanup_section.get("max_file_size_mb", 50),
            max_files=cleanup_section.get("max_files", 100),
            keep_minimum_days=cleanup_section.get("keep_minimum_days", 7),
            strategy=cleanup_section.get("strategy", "oldest_first"),
            error_log=error_log_cleanup,
        )

        log_file = LogFileConfig(
            enabled=file_section.get("enabled", True),
            directory=file_section.get("directory", "logs"),
            organize_by_date=file_section.get("organize_by_date", True),
            timestamp_format=file_section.get("timestamp_format", "%Y-%m-%d_%H%M%S"),
            format=file_section.get("format", "jsonl"),
            separate_errors=file_section.get("separate_errors", True),
            error_file=file_section.get("error_file", "errors.log"),
            performance_log=file_section.get("performance_log", True),
            cleanup=log_cleanup,
        )

        log_performance = LogPerformanceConfig(
            log_api_calls=perf_section.get("log_api_calls", True),
            log_timing=perf_section.get("log_timing", True),
            log_memory=perf_section.get("log_memory", False),
            slow_threshold_ms=perf_section.get("slow_threshold_ms", 1000),
        )

        return LoggingConfig(
            level=section.get("level", "INFO"),
            colorize=section.get("colorize", True),
            show_timestamps=section.get("show_timestamps", True),
            progress_style=section.get("progress_style", "rich"),
            file=log_file,
            performance=log_performance,
        )

    def _build_report_cleanup_config(self) -> ReportCleanupConfig:
        """Build ReportCleanupConfig from raw config."""
        section = self._raw_config.get("output_cleanup", {})
        archive_section = section.get("archive", {})

        archive = ArchiveConfig(
            enabled=archive_section.get("enabled", True),
            directory=archive_section.get("directory", "reports/archive"),
            compress=archive_section.get("compress", True),
            archive_after_days=archive_section.get("archive_after_days", 365),
        )

        return ReportCleanupConfig(
            enabled=section.get("enabled", True),
            trigger=section.get("trigger", "startup"),
            retention_years=section.get("retention_years", 2),
            keep_versions=section.get("keep_versions", 3),
            max_total_size_mb=section.get("max_total_size_mb", 1000),
            max_file_size_mb=section.get("max_file_size_mb", 100),
            max_reports=section.get("max_reports", 500),
            keep_minimum_months=section.get("keep_minimum_months", 6),
            strategy=section.get("strategy", "oldest_first"),
            archive=archive,
        )


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:  # UC-4.1 | PLAN-3.2
    """
    Load configuration as raw dictionary for backward compatibility.

    Args:
        config_path: Path to config YAML file

    Returns:
        dict: Raw configuration dictionary
    """
    config: dict[str, Any] = {}

    # Load from YAML if exists
    path = Path(config_path)
    if path.exists():
        with open(path, "r") as f:
            config = yaml.safe_load(f) or {}

    # Apply environment variables
    env_mappings = {
        "GITHUB_ACTIVITY_USER": ("user", "username"),
        "GITHUB_ACTIVITY_OUTPUT_DIR": ("output", "directory"),
        "GITHUB_ACTIVITY_LOG_LEVEL": ("logging", "level"),
        "GITHUB_ACTIVITY_LOG_DIR": ("logging", "file", "directory"),
        "GITHUB_ACTIVITY_CACHE_DIR": ("cache", "directory"),
        "GITHUB_ACTIVITY_HIGH_THRESHOLD": ("fetching", "high_activity_threshold"),
    }

    for env_var, path_tuple in env_mappings.items():
        value = os.environ.get(env_var)
        if value:
            # Convert numeric values
            if env_var == "GITHUB_ACTIVITY_HIGH_THRESHOLD":
                value = int(value)
            _set_nested(config, path_tuple, value)

    return config


def _set_nested(d: dict, path: tuple[str, ...], value: Any) -> None:
    """Set a nested dictionary value."""
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value
