# =============================================================================
# FILE: src/utils/logger.py
# TASKS: UC-9.1, UC-1.1
# PLAN: Section 3.8
# =============================================================================
"""
Structured Logger with Rich formatting.

This module provides logging with Rich formatting:

Features:
- Console output with colors (Rich)
- File output in JSONL format
- Separate error log file
- Configurable verbosity levels
- Progress bar support

Verbosity levels:
- No -v flag: INFO
- -v: DEBUG
- -vv: TRACE (all API calls)

Log file format (JSONL):
{"timestamp": "ISO", "level": "INFO", "message": "...", "context": {...}}

Error log:
- Separate file for errors
- Includes full stack traces
- Rotation when size exceeds limit

Configuration:
- logging.level: Log level
- logging.colorize: Enable colors
- logging.progress_style: "rich" | "simple" | "none"
- logging.file.directory: Log directory
- logging.file.format: "jsonl" | "text"
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.settings import LoggingConfig

# UC-9.1 | PLAN-3.8 - Custom TRACE level (lower than DEBUG)
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


class JsonFormatter(logging.Formatter):  # UC-9.1 | PLAN-3.8
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Add structured context if present
        if hasattr(record, "structured"):
            log_obj["context"] = record.structured

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
                if record.exc_info[0]
                else None,
            }

        return json.dumps(log_obj, default=str)


class ColoredFormatter(logging.Formatter):  # UC-9.1 | PLAN-3.8
    """Formatter with colored output using Rich markup."""

    COLORS = {
        "TRACE": "dim cyan",
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red",
    }

    def __init__(self, fmt: str | None = None, show_timestamps: bool = True):
        super().__init__(fmt)
        self.show_timestamps = show_timestamps

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors if available."""
        level = record.levelname
        color = self.COLORS.get(level, "white")

        # Build formatted message
        parts = []

        if self.show_timestamps:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[dim]{timestamp}[/dim]")

        parts.append(f"[{color}][{level:>8}][/{color}]")
        parts.append(f"[bold]{record.name}[/bold]:")
        parts.append(record.getMessage())

        # Add context info if present
        if hasattr(record, "structured") and record.structured:
            context_str = " ".join(
                f"{k}={v}" for k, v in record.structured.items()
            )
            parts.append(f"[dim]({context_str})[/dim]")

        return " ".join(parts)


class SimpleFormatter(logging.Formatter):  # UC-9.1 | PLAN-3.8
    """Simple text formatter without colors."""

    def __init__(self, show_timestamps: bool = True):
        self.show_timestamps = show_timestamps
        fmt = ""
        if show_timestamps:
            fmt = "%(asctime)s "
        fmt += "[%(levelname)s] %(name)s: %(message)s"
        super().__init__(fmt)


class Logger:  # UC-9.1 | PLAN-3.8
    """
    Structured logger with performance tracking and context.

    Provides:
    - Console output with optional Rich colors
    - File output in JSONL format
    - Separate error log file
    - Operation timing
    - Persistent context for all log entries

    Usage:
        logger = Logger("github-activity", config)
        logger.info("Starting report generation", user="octocat")

        # With timing
        logger.start_timer("fetch_commits")
        # ... do work ...
        logger.end_timer("fetch_commits", count=42)

        # With context
        logger.set_context(period="2024-01")
        logger.info("Processing")  # Will include period in all logs
    """

    def __init__(self, name: str, config: LoggingConfig):
        """
        Initialize logger.

        Args:
            name: Logger name (appears in log output)
            config: LoggingConfig from settings
        """
        self.name = name
        self.config = config
        self._context: dict[str, Any] = {}
        self._timers: dict[str, datetime] = {}
        self._logger: logging.Logger | None = None
        self._console = None  # Rich console, lazily initialized
        self._progress = None  # Progress bar, lazily initialized

        self._setup_handlers()

    def _setup_handlers(self) -> None:  # UC-9.1 | PLAN-3.8
        """Configure logging handlers based on config."""
        self._logger = logging.getLogger(self.name)

        # Clear any existing handlers
        self._logger.handlers.clear()

        # Set level (handle TRACE as custom level)
        level = self.config.level.upper()
        if level == "TRACE":
            self._logger.setLevel(TRACE)
        else:
            self._logger.setLevel(getattr(logging, level, logging.INFO))

        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)

        if self.config.colorize and self.config.progress_style == "rich":
            # Use Rich for colorized output
            try:
                from rich.logging import RichHandler
                console_handler = RichHandler(
                    rich_tracebacks=True,
                    show_time=self.config.show_timestamps,
                    show_path=False,
                )
            except ImportError:
                # Fall back to simple colored formatter
                console_handler.setFormatter(
                    ColoredFormatter(show_timestamps=self.config.show_timestamps)
                )
        else:
            # Use simple formatter
            console_handler.setFormatter(
                SimpleFormatter(show_timestamps=self.config.show_timestamps)
            )

        self._logger.addHandler(console_handler)

        # File handlers
        if self.config.file.enabled:
            self._setup_file_handlers()

    def _setup_file_handlers(self) -> None:  # UC-9.1 | PLAN-3.8
        """Set up file logging handlers."""
        log_dir = Path(self.config.file.directory)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main log file
        log_path = self._get_log_path()
        file_handler = logging.FileHandler(log_path, encoding="utf-8")

        if self.config.file.format == "jsonl":
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    self.config.file.timestamp_format
                    if hasattr(self.config.file, "format_str")
                    else "%(asctime)s - %(levelname)s - %(message)s"
                )
            )

        self._logger.addHandler(file_handler)

        # Separate error file
        if self.config.file.separate_errors:
            error_dir = log_dir / "errors"
            error_dir.mkdir(exist_ok=True)

            error_path = log_dir / self.config.file.error_file
            error_handler = logging.FileHandler(error_path, encoding="utf-8")
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JsonFormatter())
            self._logger.addHandler(error_handler)

    def _get_log_path(self) -> Path:  # UC-9.1 | PLAN-3.8
        """Get log file path based on config."""
        base_dir = Path(self.config.file.directory)

        if self.config.file.organize_by_date:
            now = datetime.now()
            log_dir = base_dir / str(now.year) / f"{now.month:02d}"
        else:
            log_dir = base_dir

        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime(self.config.file.timestamp_format)
        return log_dir / f"{timestamp}_activity.log"

    def set_context(self, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """
        Set persistent context for all subsequent log entries.

        Args:
            **kwargs: Key-value pairs to include in all log entries
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:  # UC-9.1 | PLAN-3.8
        """Clear all persistent context."""
        self._context.clear()

    def start_timer(self, operation: str) -> None:  # UC-9.1 | PLAN-3.8
        """
        Start timing an operation.

        Args:
            operation: Name of the operation to time
        """
        self._timers[operation] = datetime.now()

    def end_timer(self, operation: str, **extra: Any) -> float:  # UC-9.1 | PLAN-3.8
        """
        End timing and log the duration.

        Args:
            operation: Name of the operation
            **extra: Additional context to log

        Returns:
            Duration in seconds (0.0 if timer not found)
        """
        if operation not in self._timers:
            return 0.0

        duration = (datetime.now() - self._timers[operation]).total_seconds()
        duration_ms = int(duration * 1000)

        del self._timers[operation]

        # Log timing if performance logging enabled
        if self.config.performance.log_timing:
            self.debug(f"{operation} completed", duration_ms=duration_ms, **extra)

        # Warn if slow
        if duration_ms > self.config.performance.slow_threshold_ms:
            self.warning(f"{operation} slow", duration_ms=duration_ms, **extra)

        return duration

    def trace(self, msg: str, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """Log at TRACE level (most verbose)."""
        self._log(TRACE, msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """Log at DEBUG level."""
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """Log at INFO level."""
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """Log at WARNING level."""
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, exc_info: bool = False, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """
        Log at ERROR level.

        Args:
            msg: Error message
            exc_info: If True, include exception traceback
            **kwargs: Additional context
        """
        self._log(logging.ERROR, msg, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, exc_info: bool = True, **kwargs: Any) -> None:  # UC-9.1 | PLAN-3.8
        """
        Log at CRITICAL level.

        Args:
            msg: Critical error message
            exc_info: If True, include exception traceback (default True)
            **kwargs: Additional context
        """
        self._log(logging.CRITICAL, msg, exc_info=exc_info, **kwargs)

    def _log(
        self,
        level: int,
        msg: str,
        exc_info: bool = False,
        **kwargs: Any
    ) -> None:  # UC-9.1 | PLAN-3.8
        """
        Internal log method with context and extra fields.

        Args:
            level: Log level
            msg: Message to log
            exc_info: Include exception info
            **kwargs: Additional context
        """
        if self._logger is None:
            return

        # Merge context with kwargs
        extra = {**self._context, **kwargs}

        # Create log record with structured data
        self._logger.log(
            level,
            msg,
            exc_info=exc_info,
            extra={"structured": extra} if extra else {},
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        status: int | None = None,
        duration_ms: int | None = None,
        **kwargs: Any
    ) -> None:  # UC-9.1 | PLAN-3.8
        """
        Log an API call if performance logging enabled.

        Args:
            endpoint: API endpoint called
            method: HTTP method
            status: Response status code
            duration_ms: Call duration in milliseconds
            **kwargs: Additional context
        """
        if not self.config.performance.log_api_calls:
            return

        self.trace(
            f"API {method} {endpoint}",
            status=status,
            duration_ms=duration_ms,
            **kwargs
        )

    def get_progress(self, total: int, description: str = "Processing"):
        """
        Get a progress bar for iteration.

        Args:
            total: Total number of items
            description: Progress bar description

        Returns:
            Progress context manager or None if progress disabled
        """
        if self.config.progress_style == "none":
            return None

        if self.config.progress_style == "rich":
            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
                return Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                )
            except ImportError:
                pass

        # Simple progress (fallback)
        return SimpleProgress(total, description)


class SimpleProgress:  # UC-9.1 | PLAN-3.8
    """Simple progress indicator for non-Rich environments."""

    def __init__(self, total: int, description: str):
        self.total = total
        self.description = description
        self.current = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        print(file=sys.stderr)  # Newline after progress

    def advance(self, amount: int = 1):
        """Advance progress by amount."""
        self.current += amount
        pct = (self.current / self.total * 100) if self.total > 0 else 100
        print(f"\r{self.description}: {self.current}/{self.total} ({pct:.0f}%)", end="", file=sys.stderr)


def setup_logger(
    name: str = "github-activity",
    config: LoggingConfig | None = None,
    level: str | None = None,
) -> Logger:  # UC-9.1 | PLAN-3.8
    """
    Create and configure a logger instance.

    This is the main entry point for creating loggers.

    Args:
        name: Logger name
        config: LoggingConfig from settings (uses defaults if None)
        level: Override log level

    Returns:
        Configured Logger instance

    Usage:
        from src.utils.logger import setup_logger
        logger = setup_logger("github-activity", settings.logging)
        logger.info("Starting...")
    """
    if config is None:
        # Create default config
        from ..config.settings import LoggingConfig
        config = LoggingConfig()

    if level:
        config.level = level

    return Logger(name, config)
