# =============================================================================
# FILE: src/utils/log_cleanup.py
# TASKS: UC-10.1, UC-1.1
# PLAN: Section 3.9
# =============================================================================
"""
Log File Cleanup and Rotation.

This module handles log cleanup and rotation with configurable thresholds:

Cleanup triggers:
- startup: Run at application start
- shutdown: Run at application end
- both: Run at both times
- manual: Only run when explicitly called

Cleanup thresholds:
- retention_days: Delete logs older than N days
- max_total_size_mb: Delete oldest when total exceeds
- max_file_size_mb: Rotate files larger than
- max_files: Delete oldest when count exceeds

Error log rotation (NO SYMLINKS):
1. When errors.log > max_size_mb:
   - Move: errors.log -> errors/errors_{timestamp}.log
   - Compress: -> errors/errors_{timestamp}.log.gz (if enabled)
   - Create new: errors.log (empty)
2. Delete old rotated error logs based on age/count

Cross-platform notes:
- NO SYMLINKS used anywhere
- Uses direct file operations only
- Works on Windows, macOS, and Linux
"""
from __future__ import annotations

import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config.settings import LogCleanupConfig


class LogCleaner:  # UC-10.1 | PLAN-3.9
    """
    Automatic log cleanup based on configurable thresholds.

    Handles:
    - Age-based cleanup (retention_days)
    - Size-based cleanup (max_total_size_mb, max_file_size_mb)
    - Count-based cleanup (max_files)
    - Error log rotation with compression
    - Empty directory cleanup

    Usage:
        from src.utils.log_cleanup import LogCleaner
        from src.config.settings import LogCleanupConfig

        config = LogCleanupConfig(retention_days=30, max_files=100)
        cleaner = LogCleaner(Path("logs"), config)
        stats = cleaner.clean()
        print(f"Deleted {stats['deleted']} files, freed {stats['freed_mb']:.2f} MB")
    """

    def __init__(self, logs_dir: Path, config: LogCleanupConfig):
        """
        Initialize log cleaner.

        Args:
            logs_dir: Path to logs directory
            config: LogCleanupConfig from settings
        """
        self.logs_dir = Path(logs_dir)
        self.config = config
        self.stats: dict[str, Any] = {
            "deleted": 0,
            "rotated": 0,
            "compressed": 0,
            "freed_mb": 0.0,
        }

    def clean(self) -> dict[str, Any]:  # UC-10.1 | PLAN-3.9
        """
        Run all cleanup operations and return statistics.

        Operations are run in this order:
        1. Handle error log rotation (size-based)
        2. Delete logs by age (retention_days)
        3. Delete logs by total size (max_total_size_mb)
        4. Delete logs by count (max_files)
        5. Remove empty directories

        Returns:
            dict with cleanup statistics:
            - deleted: Number of files deleted
            - rotated: Number of error logs rotated
            - compressed: Number of files compressed
            - freed_mb: MB of space freed
        """
        if not self.logs_dir.exists():
            return self.stats

        # Step 1: Handle error log rotation first
        self._handle_error_log_rotation()

        # Step 2: Clean up old rotated error logs
        self._cleanup_old_error_logs()

        # Step 3: Delete by age
        self._cleanup_by_age()

        # Step 4: Delete oversized individual files and by total size
        self._cleanup_by_size()

        # Step 5: Delete by count
        self._cleanup_by_count()

        # Step 6: Remove empty directories
        self._remove_empty_directories()

        return self.stats

    def _handle_error_log_rotation(self) -> None:  # UC-10.1 | PLAN-3.9
        """
        Handle error log rotation by size.

        When errors.log exceeds max_size_mb:
        1. Move to errors/ directory with timestamp
        2. Compress if compress_rotated is True
        3. Create new empty errors.log

        NO SYMLINKS are used - just direct file operations.
        """
        error_log = self.logs_dir / "errors.log"

        # Ensure errors directory exists
        errors_dir = self.logs_dir / "errors"
        errors_dir.mkdir(exist_ok=True)

        # Create error log if it doesn't exist
        if not error_log.exists():
            error_log.touch()
            return

        # Check if rotation needed
        max_bytes = self.config.error_log.max_size_mb * 1024 * 1024
        if error_log.stat().st_size <= max_bytes:
            return

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        rotated_name = f"errors_{timestamp}.log"
        rotated_path = errors_dir / rotated_name

        # Move current log to errors/ directory (no symlinks)
        shutil.move(str(error_log), str(rotated_path))
        self.stats["rotated"] += 1

        # Compress if enabled
        if self.config.error_log.compress_rotated:
            compressed_path = Path(f"{rotated_path}.gz")
            with open(rotated_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            rotated_path.unlink()  # Remove uncompressed version
            self.stats["compressed"] += 1

        # Create new empty error log
        error_log.touch()

    def _cleanup_old_error_logs(self) -> None:  # UC-10.1 | PLAN-3.9
        """Delete old rotated error logs based on age and count."""
        errors_dir = self.logs_dir / "errors"
        if not errors_dir.exists():
            return

        # Get all error log files
        error_files = sorted(
            list(errors_dir.glob("errors_*.log*")),
            key=lambda f: f.stat().st_mtime,
        )

        # Delete by age
        cutoff = datetime.now() - timedelta(days=self.config.error_log.max_age_days)

        for f in error_files[:]:
            try:
                # Extract date from filename: errors_2024-01-15_120000.log(.gz)
                date_part = f.stem.replace("errors_", "").split("_")[0]
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if file_date < cutoff:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    f.unlink()
                    error_files.remove(f)
                    self.stats["deleted"] += 1
                    self.stats["freed_mb"] += size_mb
            except (ValueError, IndexError):
                # Skip files that don't match expected format
                pass

        # Delete by count (keep only max_files)
        while len(error_files) > self.config.error_log.max_files:
            oldest = error_files.pop(0)
            size_mb = oldest.stat().st_size / (1024 * 1024)
            oldest.unlink()
            self.stats["deleted"] += 1
            self.stats["freed_mb"] += size_mb

    def _cleanup_by_age(self) -> None:  # UC-10.1 | PLAN-3.9
        """Delete logs older than retention threshold."""
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        minimum_cutoff = datetime.now() - timedelta(days=self.config.keep_minimum_days)

        # Also handle performance logs with different retention
        perf_cutoff = datetime.now() - timedelta(
            days=self.config.retention_days_performance
        )

        for log_file in self._get_activity_logs():
            # Skip if within minimum keep period
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime >= minimum_cutoff:
                continue

            # Use different threshold for performance logs
            threshold = perf_cutoff if "_performance" in log_file.name else cutoff

            if mtime < threshold:
                self._delete_file(log_file)

    def _cleanup_by_size(self) -> None:  # UC-10.1 | PLAN-3.9
        """Delete logs if total size or individual file size exceeds threshold."""
        max_total_bytes = self.config.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.config.max_file_size_mb * 1024 * 1024

        # Delete oversized individual files first
        for log_file in self._get_activity_logs():
            if log_file.stat().st_size > max_file_bytes:
                self._delete_file(log_file)

        # Check total size
        total_size = sum(
            f.stat().st_size for f in self._get_activity_logs()
        )

        if total_size > max_total_bytes:
            bytes_to_free = total_size - max_total_bytes
            self._free_space_by_strategy(bytes_to_free)

    def _cleanup_by_count(self) -> None:  # UC-10.1 | PLAN-3.9
        """Delete logs if file count exceeds threshold."""
        log_files = sorted(
            list(self._get_activity_logs()),
            key=lambda f: f.stat().st_mtime,
        )

        while len(log_files) > self.config.max_files:
            oldest = log_files.pop(0)
            self._delete_file(oldest)

    def _free_space_by_strategy(self, bytes_to_free: int) -> None:  # UC-10.1 | PLAN-3.9
        """Free up space using configured strategy."""
        log_files = list(self._get_activity_logs())

        if self.config.strategy == "oldest_first":
            log_files.sort(key=lambda f: f.stat().st_mtime)
        elif self.config.strategy == "largest_first":
            log_files.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for log_file in log_files:
            if freed >= bytes_to_free:
                break
            freed += log_file.stat().st_size
            self._delete_file(log_file)

    def _get_activity_logs(self):  # UC-10.1 | PLAN-3.9
        """
        Get all activity log files (excluding errors.log).

        Yields:
            Path objects for each log file
        """
        for log_file in self.logs_dir.rglob("*.log"):
            # Skip main error log and rotated error logs
            if log_file.name == "errors.log":
                continue
            if log_file.parent.name == "errors":
                continue
            yield log_file

    def _delete_file(self, file_path: Path) -> None:  # UC-10.1 | PLAN-3.9
        """Delete a file and update stats."""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            self.stats["deleted"] += 1
            self.stats["freed_mb"] += size_mb
        except (OSError, FileNotFoundError):
            # File may have been deleted by another process
            pass

    def _remove_empty_directories(self) -> None:  # UC-10.1 | PLAN-3.9
        """Remove empty log directories."""
        # Sort in reverse to process deepest directories first
        for dir_path in sorted(self.logs_dir.rglob("*"), reverse=True):
            if dir_path.is_dir():
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except OSError:
                    # Directory not empty or permission issue
                    pass


def cleanup_logs(
    logs_dir: Path | str,
    config: LogCleanupConfig | None = None,
) -> dict[str, Any]:  # UC-10.1 | PLAN-3.9
    """
    Convenience function to clean up logs.

    Args:
        logs_dir: Path to logs directory
        config: LogCleanupConfig (uses defaults if None)

    Returns:
        Cleanup statistics dict
    """
    if config is None:
        from ..config.settings import LogCleanupConfig
        config = LogCleanupConfig()

    cleaner = LogCleaner(Path(logs_dir), config)
    return cleaner.clean()
