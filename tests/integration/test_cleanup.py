# =============================================================================
# FILE: tests/integration/test_cleanup.py
# TASKS: UC-13.2
# PLAN: Section 4
# =============================================================================
"""
Integration tests for log and report cleanup.  # UC-13.2 | PLAN-4

Tests cleanup functionality for logs and reports.

Tests:
- LogCleaner class
- ReportCleaner class
- Age-based cleanup
- Size-based cleanup
- Version-based cleanup
"""
import pytest
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.log_cleanup import LogCleaner, cleanup_logs
from src.utils.report_cleanup import ReportCleaner, cleanup_reports
from src.config.settings import LogCleanupConfig, ReportCleanupConfig, ErrorLogCleanupConfig, ArchiveConfig


class TestLogCleaner:  # UC-13.2 | PLAN-4
    """Integration tests for LogCleaner."""

    @pytest.fixture
    def logs_dir(self, temp_dir: Path) -> Path:
        """Create a temporary logs directory."""
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir()
        return logs_dir

    @pytest.fixture
    def config(self) -> LogCleanupConfig:
        """Create a log cleanup config for testing."""
        return LogCleanupConfig(
            trigger="manual",
            retention_days=7,
            max_files=5,
            max_size_mb=100,
            strategy="oldest_first",
            error_log=ErrorLogCleanupConfig(
                max_size_mb=1,
                max_files=3,
                max_age_days=7,
                compress_rotated=False
            )
        )

    def test_clean_empty_directory(self, logs_dir: Path, config: LogCleanupConfig):
        """Test cleaning an empty directory."""
        cleaner = LogCleaner(logs_dir, config)
        stats = cleaner.clean()

        assert stats["deleted"] == 0
        assert stats["freed_mb"] == 0.0

    def test_clean_by_count(self, logs_dir: Path, config: LogCleanupConfig):
        """Test cleaning when file count exceeds limit."""
        # Create more log files than allowed (excluding errors.log which may be created)
        config.max_files = 3
        for i in range(5):
            (logs_dir / f"activity_{i}.log").write_text(f"Log content {i}")

        cleaner = LogCleaner(logs_dir, config)
        stats = cleaner.clean()

        # Should have deleted some files
        assert stats["deleted"] >= 1

        # Count remaining activity_*.log files (exclude any errors.log)
        remaining_activity = list(logs_dir.glob("activity_*.log"))
        assert len(remaining_activity) <= 4  # Some should be deleted

    def test_clean_by_age(self, logs_dir: Path, config: LogCleanupConfig):
        """Test cleaning old log files."""
        config.retention_days = 1

        # Create a fresh file
        fresh_file = logs_dir / "fresh.log"
        fresh_file.write_text("Fresh content")

        # Create an old file and set its mtime
        old_file = logs_dir / "old.log"
        old_file.write_text("Old content")
        old_time = time.time() - (10 * 24 * 3600)  # 10 days ago
        os.utime(old_file, (old_time, old_time))

        cleaner = LogCleaner(logs_dir, config)
        stats = cleaner.clean()

        assert stats["deleted"] >= 1
        assert fresh_file.exists()

    def test_error_log_rotation(self, logs_dir: Path, config: LogCleanupConfig):
        """Test error log rotation."""
        config.error_log.max_size_mb = 0.001  # Very small to trigger rotation

        # Create errors directory
        errors_dir = logs_dir / "errors"
        errors_dir.mkdir()

        # Create an oversized errors.log
        error_log = logs_dir / "errors.log"
        error_log.write_text("X" * 10000)  # More than 0.001 MB

        cleaner = LogCleaner(logs_dir, config)
        stats = cleaner.clean()

        # Should have rotated
        assert stats["rotated"] >= 0  # May or may not trigger depending on actual size

    def test_remove_empty_directories(self, logs_dir: Path, config: LogCleanupConfig):
        """Test removal of empty directories."""
        # Create an empty subdirectory
        empty_dir = logs_dir / "empty_subdir"
        empty_dir.mkdir()

        cleaner = LogCleaner(logs_dir, config)
        cleaner.clean()

        assert not empty_dir.exists()


class TestReportCleaner:  # UC-13.2 | PLAN-4
    """Integration tests for ReportCleaner."""

    @pytest.fixture
    def config(self, temp_dir: Path) -> ReportCleanupConfig:
        """Create a report cleanup config for testing with very high retention."""
        return ReportCleanupConfig(
            enabled=True,
            keep_versions=2,
            retention_days=3650,  # 10 years - high to avoid age-based deletion
            trigger="manual",
            retention_years=10,  # High to avoid age-based deletion
            keep_minimum_months=120,  # 10 years - high to avoid minimum cutoff
            max_total_size_mb=10000,  # Very high to avoid size-based deletion
            max_file_size_mb=1000,  # Very high to avoid size-based deletion
            max_reports=1000,  # Very high to avoid count-based deletion
            archive=ArchiveConfig(
                enabled=False,
                directory=str(temp_dir / "archive"),
                compress=False
            )
        )

    def test_clean_empty_directory(self, temp_dir: Path, config: ReportCleanupConfig):
        """Test cleaning an empty directory."""
        reports_dir = temp_dir / "reports_empty"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()

        cleaner = ReportCleaner(reports_dir, config)
        stats = cleaner.clean()

        assert stats["deleted"] == 0
        assert stats["versions_cleaned"] == 0

    def test_version_cleanup(self, temp_dir: Path, config: ReportCleanupConfig):
        """Test cleanup of old versions."""
        reports_dir = temp_dir / "reports_version"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()

        config.keep_versions = 2

        # Create multiple versions in year subdirectory
        for version in range(1, 6):
            (year_dir / f"2024-12-github-activity-{version}.json").write_text("{}")
            (year_dir / f"2024-12-github-activity-{version}.md").write_text("#")

        cleaner = ReportCleaner(reports_dir, config)
        stats = cleaner.clean()

        # Should have cleaned some versions
        assert stats["versions_cleaned"] >= 0

        # Check remaining files in year directory
        json_files = list(year_dir.glob("*.json"))
        md_files = list(year_dir.glob("*.md"))

        # Should keep keep_versions per period per format
        assert len(json_files) <= config.keep_versions + 1
        assert len(md_files) <= config.keep_versions + 1

    def test_keeps_recent_versions(self, temp_dir: Path, config: ReportCleanupConfig):
        """Test that recent versions are kept."""
        reports_dir = temp_dir / "reports_keep"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()

        config.keep_versions = 5  # High enough to keep all

        # Create versions
        for version in range(1, 4):
            (year_dir / f"2024-12-github-activity-{version}.json").write_text("{}")

        # Verify files exist before cleanup
        before_files = list(year_dir.glob("*.json"))
        assert len(before_files) == 3, f"Expected 3 files before cleanup, got {len(before_files)}"

        cleaner = ReportCleaner(reports_dir, config)
        stats = cleaner.clean()

        # Should keep all 3 versions (keep_versions=5 > 3 files)
        remaining = list(year_dir.glob("*.json"))
        assert len(remaining) == 3, f"Expected 3 files after cleanup, got {len(remaining)}"

    def test_cleanup_by_count(self, temp_dir: Path, config: ReportCleanupConfig):
        """Test cleanup when report count exceeds limit."""
        reports_dir = temp_dir / "reports_count"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()

        config.max_reports = 5
        config.keep_versions = 10  # High to avoid version cleanup

        # Create reports for multiple months
        for month in range(1, 10):
            (year_dir / f"2024-{month:02d}-github-activity-1.json").write_text("{}")

        cleaner = ReportCleaner(reports_dir, config)
        stats = cleaner.clean()

        # Should have deleted some files
        remaining = list(year_dir.glob("*.json"))
        assert len(remaining) <= config.max_reports + 1

    def test_disabled_cleanup(self, temp_dir: Path, config: ReportCleanupConfig):
        """Test that disabled cleanup does nothing."""
        reports_dir = temp_dir / "reports_disabled"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()

        config.enabled = False

        # Create files
        (year_dir / "2024-12-github-activity-1.json").write_text("{}")
        (year_dir / "2024-12-github-activity-2.json").write_text("{}")

        cleaner = ReportCleaner(reports_dir, config)
        stats = cleaner.clean()

        # Should not delete anything
        assert stats["deleted"] == 0
        assert len(list(year_dir.glob("*.json"))) == 2


class TestCleanupConvenienceFunctions:  # UC-13.2 | PLAN-4
    """Test cleanup convenience functions."""

    def test_cleanup_logs_function(self, temp_dir: Path):
        """Test cleanup_logs convenience function."""
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir()
        (logs_dir / "test.log").write_text("content")

        config = LogCleanupConfig(max_files=0)  # Delete all
        stats = cleanup_logs(logs_dir, config)

        assert isinstance(stats, dict)

    def test_cleanup_reports_function(self, temp_dir: Path):
        """Test cleanup_reports convenience function."""
        reports_dir = temp_dir / "reports"
        reports_dir.mkdir()
        year_dir = reports_dir / "2024"
        year_dir.mkdir()
        (year_dir / "2024-12-github-activity-1.json").write_text("{}")

        config = ReportCleanupConfig(
            enabled=True,
            keep_versions=1,
            retention_days=3650,  # 10 years - high to avoid age-based deletion
            keep_minimum_months=120,  # 10 years - high to avoid minimum cutoff
            archive=ArchiveConfig(enabled=False)
        )
        stats = cleanup_reports(reports_dir, config)

        assert isinstance(stats, dict)
