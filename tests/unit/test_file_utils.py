# =============================================================================
# FILE: tests/unit/test_file_utils.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for file utility functions.  # UC-13.1 | PLAN-4

Tests:
- ensure_dir: Directory creation
- safe_write: Safe file writing
- get_next_version: Version number calculation
- get_next_filename: Filename generation
"""
import pytest
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.file_utils import (
    ensure_dir,
    safe_write,
    get_next_version,
    get_next_filename,
)


class TestEnsureDir:  # UC-13.1 | PLAN-4
    """Tests for ensure_dir function."""

    def test_creates_directory_if_not_exists(self, temp_dir: Path):
        """Test that directory is created if it doesn't exist."""
        new_dir = temp_dir / "new_directory"
        assert not new_dir.exists()

        result = ensure_dir(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_creates_nested_directories(self, temp_dir: Path):
        """Test that nested directories are created."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        result = ensure_dir(nested_dir)

        assert nested_dir.exists()
        assert result == nested_dir

    def test_returns_existing_directory(self, temp_dir: Path):
        """Test that existing directory is returned without error."""
        result = ensure_dir(temp_dir)

        assert result == temp_dir
        assert temp_dir.exists()

    def test_accepts_string_path(self, temp_dir: Path):
        """Test that string paths are accepted."""
        new_dir = temp_dir / "string_path_test"
        result = ensure_dir(str(new_dir))

        assert new_dir.exists()
        assert result == new_dir


class TestSafeWrite:  # UC-13.1 | PLAN-4
    """Tests for safe_write function."""

    def test_writes_content_to_file(self, temp_dir: Path):
        """Test that content is written to file."""
        file_path = temp_dir / "test.txt"
        content = "Hello, World!"

        safe_write(file_path, content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_creates_parent_directories(self, temp_dir: Path):
        """Test that parent directories are created."""
        file_path = temp_dir / "subdir" / "nested" / "test.txt"
        content = "Nested content"

        safe_write(file_path, content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_overwrites_existing_file(self, temp_dir: Path):
        """Test that existing file is overwritten."""
        file_path = temp_dir / "existing.txt"
        file_path.write_text("Original content")

        safe_write(file_path, "New content")

        assert file_path.read_text() == "New content"

    def test_accepts_string_path(self, temp_dir: Path):
        """Test that string paths are accepted."""
        file_path = temp_dir / "string_path.txt"
        safe_write(str(file_path), "Test")

        assert file_path.exists()

    def test_returns_path(self, temp_dir: Path):
        """Test that function returns the path."""
        file_path = temp_dir / "return_test.txt"
        result = safe_write(file_path, "Content")

        assert result == file_path

    def test_writes_dict_as_json(self, temp_dir: Path):
        """Test that dictionaries are written as JSON."""
        file_path = temp_dir / "test.json"
        data = {"key": "value", "number": 42}

        safe_write(file_path, data)

        assert file_path.exists()
        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data


class TestGetNextVersion:  # UC-13.1 | PLAN-4
    """Tests for get_next_version function."""

    def test_returns_1_for_empty_directory(self, temp_dir: Path):
        """Test that 1 is returned for empty directory."""
        result = get_next_version(temp_dir, "2024-12-github-activity", "json")
        assert result == 1

    def test_returns_1_for_nonexistent_directory(self, temp_dir: Path):
        """Test that 1 is returned for non-existent directory."""
        nonexistent = temp_dir / "nonexistent"
        nonexistent.mkdir()  # Create directory but leave empty
        result = get_next_version(nonexistent, "2024-12-github-activity", "json")
        assert result == 1

    def test_increments_version(self, temp_dir: Path):
        """Test that version is incremented correctly."""
        # Create existing version
        (temp_dir / "2024-12-github-activity-1.json").touch()

        result = get_next_version(temp_dir, "2024-12-github-activity", "json")
        assert result == 2

    def test_handles_multiple_versions(self, temp_dir: Path):
        """Test handling multiple existing versions."""
        # Create multiple versions
        (temp_dir / "2024-12-github-activity-1.json").touch()
        (temp_dir / "2024-12-github-activity-2.json").touch()
        (temp_dir / "2024-12-github-activity-3.json").touch()

        result = get_next_version(temp_dir, "2024-12-github-activity", "json")
        assert result == 4

    def test_handles_gaps_in_versions(self, temp_dir: Path):
        """Test handling gaps in version numbers."""
        # Create versions with gaps
        (temp_dir / "2024-12-github-activity-1.json").touch()
        (temp_dir / "2024-12-github-activity-5.json").touch()

        result = get_next_version(temp_dir, "2024-12-github-activity", "json")
        assert result == 6  # Should use highest + 1

    def test_different_periods_independent(self, temp_dir: Path):
        """Test that different periods have independent versions."""
        # Create versions for different periods
        (temp_dir / "2024-11-github-activity-5.json").touch()
        (temp_dir / "2024-12-github-activity-1.json").touch()

        result = get_next_version(temp_dir, "2024-12-github-activity", "json")
        assert result == 2

    def test_quarterly_period(self, temp_dir: Path):
        """Test versioning for quarterly period."""
        (temp_dir / "2024-Q4-github-activity-1.json").touch()

        result = get_next_version(temp_dir, "2024-Q4-github-activity", "json")
        assert result == 2


class TestGetNextFilename:  # UC-13.1 | PLAN-4
    """Tests for get_next_filename function."""

    def test_generates_json_filename(self, temp_dir: Path):
        """Test JSON filename generation."""
        result = get_next_filename(temp_dir, 2024, "monthly", 12, "json")
        assert result.name == "2024-12-github-activity-1.json"

    def test_generates_markdown_filename(self, temp_dir: Path):
        """Test Markdown filename generation."""
        result = get_next_filename(temp_dir, 2024, "monthly", 12, "md")
        assert result.name == "2024-12-github-activity-1.md"

    def test_quarterly_filename(self, temp_dir: Path):
        """Test quarterly filename generation."""
        result = get_next_filename(temp_dir, 2024, "quarterly", 4, "json")
        assert result.name == "2024-Q4-github-activity-1.json"

    def test_monthly_with_leading_zero(self, temp_dir: Path):
        """Test monthly filename has leading zero for single-digit months."""
        result = get_next_filename(temp_dir, 2024, "monthly", 1, "json")
        assert result.name == "2024-01-github-activity-1.json"

    def test_version_number_increments(self, temp_dir: Path):
        """Test that version number increments when file exists."""
        # Create year directory and first version
        year_dir = temp_dir / "2024"
        year_dir.mkdir()
        (year_dir / "2024-12-github-activity-1.json").touch()

        result = get_next_filename(temp_dir, 2024, "monthly", 12, "json")
        assert result.name == "2024-12-github-activity-2.json"

    def test_creates_year_directory(self, temp_dir: Path):
        """Test that year directory is created."""
        result = get_next_filename(temp_dir, 2024, "monthly", 12, "json")
        year_dir = temp_dir / "2024"
        assert year_dir.exists()
        assert year_dir.is_dir()
