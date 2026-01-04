# =============================================================================
# FILE: src/utils/report_cleanup.py
# TASKS: UC-11.1, UC-1.1
# PLAN: Section 3.10
# =============================================================================
"""
Report File Cleanup and Versioning.

This module handles report cleanup and archival with configurable thresholds:

Version Cleanup:
- Keep only N versions per period (e.g., keep -3, -4, -5; delete -1, -2)
- Pattern: {year}-{MM}-github-activity-{n}.{ext} or {year}-Q{Q}-github-activity-{n}.{ext}

Cleanup thresholds:
- retention_days: Delete reports older than N days (alternative to retention_years * 365)
- keep_versions: Keep last N versions per period
- max_total_size_mb: Delete oldest when total exceeds
- max_file_size_mb: Delete files larger than
- max_reports: Delete oldest when count exceeds
- keep_minimum_months: Always keep at least N months

Archive settings:
- archive.enabled: Archive old reports instead of delete
- archive.directory: Archive location
- archive.compress: Compress archived reports (.gz)
- archive.archive_after_days: Archive reports older than N days

Cross-platform notes:
- NO SYMLINKS used anywhere
- Uses direct file operations only
- Works on Windows, macOS, and Linux
"""
from __future__ import annotations

import gzip
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config.settings import ReportCleanupConfig


class ReportCleaner:  # UC-11.1 | PLAN-3.10
    """
    Automatic report cleanup based on configurable thresholds.

    Handles:
    - Version-based cleanup (keep_versions per period)
    - Age-based cleanup (retention_days/retention_years)
    - Size-based cleanup (max_total_size_mb, max_file_size_mb)
    - Count-based cleanup (max_reports)
    - Archival with compression
    - Empty directory cleanup

    Report filename pattern:
    - Monthly: {year}-{MM}-github-activity-{n}.{ext}
    - Quarterly: {year}-Q{Q}-github-activity-{n}.{ext}

    Usage:
        from src.utils.report_cleanup import ReportCleaner
        from src.config.settings import ReportCleanupConfig

        config = ReportCleanupConfig(keep_versions=3, retention_days=90)
        cleaner = ReportCleaner(Path("reports"), config)
        stats = cleaner.clean()
        print(f"Deleted {stats['deleted']}, archived {stats['archived']}")
    """

    # Pattern: 2024-12-github-activity-1.md or 2024-Q4-github-activity-2.json
    REPORT_PATTERN = re.compile(
        r"(\d{4})-(\d{2}|Q[1-4])-github-activity-(\d+)\.(md|json)"
    )

    def __init__(self, reports_dir: Path, config: ReportCleanupConfig):
        """
        Initialize report cleaner.

        Args:
            reports_dir: Path to reports directory
            config: ReportCleanupConfig from settings
        """
        self.reports_dir = Path(reports_dir)
        self.config = config
        self.stats: dict[str, Any] = {
            "deleted": 0,
            "archived": 0,
            "versions_cleaned": 0,
            "freed_mb": 0.0,
        }

    def clean(self) -> dict[str, Any]:  # UC-11.1 | PLAN-3.10
        """
        Run all cleanup operations and return statistics.

        Operations are run in this order:
        1. Clean old versions (keep only keep_versions per period)
        2. Archive old reports (if archive.enabled)
        3. Delete reports by age (retention_days)
        4. Delete reports by size (max_total_size_mb, max_file_size_mb)
        5. Delete reports by count (max_reports)
        6. Remove empty directories

        Returns:
            dict with cleanup statistics:
            - deleted: Number of files deleted
            - archived: Number of files archived
            - versions_cleaned: Number of old versions removed
            - freed_mb: MB of space freed
        """
        if not self.config.enabled:
            return self.stats

        if not self.reports_dir.exists():
            return self.stats

        # Step 1: Clean old versions first
        self._cleanup_old_versions()

        # Step 2: Archive old reports (before deletion)
        if self.config.archive.enabled:
            self._archive_old_reports()

        # Step 3: Delete by age
        self._cleanup_by_age()

        # Step 4: Delete oversized individual files and by total size
        self._cleanup_by_size()

        # Step 5: Delete by count
        self._cleanup_by_count()

        # Step 6: Remove empty directories
        self._remove_empty_directories()

        return self.stats

    def _cleanup_old_versions(self) -> None:  # UC-11.1 | PLAN-3.10
        """
        Keep only the last N versions of each period's report.

        For example, if keep_versions=3 and we have:
        - 2024-12-github-activity-1.md
        - 2024-12-github-activity-2.md
        - 2024-12-github-activity-3.md
        - 2024-12-github-activity-4.md
        - 2024-12-github-activity-5.md

        We keep: -3, -4, -5 (highest 3)
        We delete: -1, -2

        Note: Reports are grouped by directory + period, so different users'
        reports are kept separate (e.g., reports/2025/user1/ vs reports/2025/user2/)
        """
        # Group reports by directory + period (handles user subdirectories)
        reports_by_period: dict[str, list[tuple[int, Path]]] = {}

        for report_file in self._get_all_reports():
            match = self.REPORT_PATTERN.match(report_file.name)
            if not match:
                continue

            year, period, version_str, ext = match.groups()
            # Include parent directory in key to separate users
            parent_dir = str(report_file.parent)
            period_key = f"{parent_dir}/{year}-{period}-{ext}"
            version = int(version_str)

            if period_key not in reports_by_period:
                reports_by_period[period_key] = []
            reports_by_period[period_key].append((version, report_file))

        # Delete old versions, keep only the last N
        for period_key, versions in reports_by_period.items():
            # Sort by version number descending (newest first)
            versions.sort(key=lambda x: x[0], reverse=True)

            # Delete versions beyond keep_versions
            for version_num, report_file in versions[self.config.keep_versions:]:
                self._delete_file(report_file)
                self.stats["versions_cleaned"] += 1

    def _archive_old_reports(self) -> None:  # UC-11.1 | PLAN-3.10
        """
        Archive old reports instead of deleting.

        Reports older than archive_after_days are moved to archive directory
        and optionally compressed.
        """
        cutoff = datetime.now() - timedelta(days=self.config.archive.archive_after_days)
        minimum_cutoff = datetime.now() - timedelta(
            days=self.config.keep_minimum_months * 30
        )

        archive_dir = Path(self.config.archive.directory)
        archive_dir.mkdir(parents=True, exist_ok=True)

        for report_file in list(self._get_all_reports()):
            file_date = self._get_report_date(report_file)

            # Skip if no date extracted or within minimum keep period
            if file_date is None or file_date >= minimum_cutoff:
                continue

            # Archive if older than threshold
            if file_date < cutoff:
                self._archive_file(report_file, archive_dir)

    def _archive_file(self, file_path: Path, archive_dir: Path) -> None:  # UC-11.1 | PLAN-3.10
        """
        Archive a single file.

        Args:
            file_path: Path to file to archive
            archive_dir: Destination archive directory
        """
        if self.config.archive.compress:
            # Compress and move
            dest = archive_dir / f"{file_path.name}.gz"
            with open(file_path, "rb") as f_in:
                with gzip.open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Move without compression
            dest = archive_dir / file_path.name
            shutil.copy2(file_path, dest)

        # Remove original
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_path.unlink()
        self.stats["archived"] += 1
        self.stats["freed_mb"] += size_mb

    def _cleanup_by_age(self) -> None:  # UC-11.1 | PLAN-3.10
        """Delete reports older than retention threshold."""
        # Use retention_days if available, otherwise calculate from retention_years
        retention_days = getattr(self.config, 'retention_days', None)
        if retention_days is None:
            retention_days = self.config.retention_years * 365

        cutoff = datetime.now() - timedelta(days=retention_days)
        minimum_cutoff = datetime.now() - timedelta(
            days=self.config.keep_minimum_months * 30
        )

        for report_file in list(self._get_all_reports()):
            file_date = self._get_report_date(report_file)

            # Skip if no date extracted or within minimum keep period
            if file_date is None or file_date >= minimum_cutoff:
                continue

            # Delete if older than cutoff
            if file_date < cutoff:
                self._delete_file(report_file)

    def _cleanup_by_size(self) -> None:  # UC-11.1 | PLAN-3.10
        """Delete reports if total size or individual file size exceeds threshold."""
        max_total_bytes = self.config.max_total_size_mb * 1024 * 1024
        max_file_bytes = self.config.max_file_size_mb * 1024 * 1024

        # Delete oversized individual files first
        for report_file in list(self._get_all_reports()):
            try:
                if report_file.stat().st_size > max_file_bytes:
                    self._delete_file(report_file)
            except (OSError, FileNotFoundError):
                pass

        # Check total size
        total_size = sum(
            f.stat().st_size for f in self._get_all_reports()
            if f.exists()
        )

        if total_size > max_total_bytes:
            bytes_to_free = total_size - max_total_bytes
            self._free_space_by_strategy(bytes_to_free)

    def _cleanup_by_count(self) -> None:  # UC-11.1 | PLAN-3.10
        """Delete reports if file count exceeds threshold."""
        reports = sorted(
            [f for f in self._get_all_reports() if f.exists()],
            key=lambda f: f.stat().st_mtime,
        )

        while len(reports) > self.config.max_reports:
            oldest = reports.pop(0)
            self._delete_file(oldest)

    def _free_space_by_strategy(self, bytes_to_free: int) -> None:  # UC-11.1 | PLAN-3.10
        """Free up space using configured strategy."""
        reports = [f for f in self._get_all_reports() if f.exists()]

        if self.config.strategy == "oldest_first":
            reports.sort(key=lambda f: f.stat().st_mtime)
        elif self.config.strategy == "largest_first":
            reports.sort(key=lambda f: f.stat().st_size, reverse=True)

        freed = 0
        for report_file in reports:
            if freed >= bytes_to_free:
                break
            try:
                freed += report_file.stat().st_size
                self._delete_file(report_file)
            except (OSError, FileNotFoundError):
                pass

    def _get_all_reports(self):  # UC-11.1 | PLAN-3.10
        """
        Get all report files (md and json).

        Yields:
            Path objects for each report file
        """
        for pattern in ["*.md", "*.json"]:
            for report_file in self.reports_dir.rglob(pattern):
                # Skip archived files
                if self.config.archive.directory in str(report_file):
                    continue
                yield report_file

    def _get_report_date(self, file_path: Path) -> datetime | None:  # UC-11.1 | PLAN-3.10
        """
        Extract date from report filename.

        Args:
            file_path: Path to report file

        Returns:
            datetime for the report period, or None if cannot parse
        """
        match = self.REPORT_PATTERN.match(file_path.name)
        if not match:
            return None

        year_str, period, _, _ = match.groups()
        try:
            year = int(year_str)
            if period.startswith("Q"):
                # Quarterly: use first month of quarter
                quarter = int(period[1])
                month = (quarter - 1) * 3 + 1
            else:
                # Monthly
                month = int(period)
            return datetime(year, month, 1)
        except (ValueError, IndexError):
            return None

    def _delete_file(self, file_path: Path) -> None:  # UC-11.1 | PLAN-3.10
        """Delete a file and update stats."""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            self.stats["deleted"] += 1
            self.stats["freed_mb"] += size_mb
        except (OSError, FileNotFoundError):
            # File may have been deleted by another process
            pass

    def _remove_empty_directories(self) -> None:  # UC-11.1 | PLAN-3.10
        """Remove empty report directories."""
        # Sort in reverse to process deepest directories first
        for dir_path in sorted(self.reports_dir.rglob("*"), reverse=True):
            if dir_path.is_dir():
                # Skip archive directory
                if self.config.archive.directory in str(dir_path):
                    continue
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except OSError:
                    # Directory not empty or permission issue
                    pass


def cleanup_reports(
    reports_dir: Path | str,
    config: ReportCleanupConfig | None = None,
) -> dict[str, Any]:  # UC-11.1 | PLAN-3.10
    """
    Convenience function to clean up reports.

    Args:
        reports_dir: Path to reports directory
        config: ReportCleanupConfig (uses defaults if None)

    Returns:
        Cleanup statistics dict
    """
    if config is None:
        from ..config.settings import ReportCleanupConfig
        config = ReportCleanupConfig()

    cleaner = ReportCleaner(Path(reports_dir), config)
    return cleaner.clean()
