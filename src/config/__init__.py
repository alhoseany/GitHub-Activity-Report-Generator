# =============================================================================
# FILE: src/config/__init__.py
# TASKS: UC-2.1, UC-2.5
# PLAN: Section 2, 3
# =============================================================================
"""
Configuration Package.

This package provides configuration management for the GitHub Activity Report
Generator:
- settings.py: Dataclass definitions for all configuration sections
- loader.py: Configuration loading with priority handling (CLI > ENV > YAML)
- schema.json: JSON schema for report validation

Usage:
    from src.config import ConfigLoader, Settings, load_config
"""
# UC-2.1, UC-2.5

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
    ReportCleanupConfig,
)
from .loader import ConfigLoader, load_config

__all__ = [
    "Settings",
    "PeriodConfig",
    "UserConfig",
    "RepositoryConfig",
    "FetchingConfig",
    "CacheConfig",
    "OutputConfig",
    "MetricsConfig",
    "LoggingConfig",
    "LogFileConfig",
    "LogCleanupConfig",
    "ReportCleanupConfig",
    "ConfigLoader",
    "load_config",
]
