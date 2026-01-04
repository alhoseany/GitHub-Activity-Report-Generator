# =============================================================================
# FILE: tests/unit/test_validators.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for schema validation.  # UC-13.1 | PLAN-4

Tests:
- ReportValidator class
- validate() method
- validate_file() method
- Error message formatting
- Edge cases
"""
import pytest
import json
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.reporters.validator import (
    ReportValidator,
    validate_report,
    validate_report_file,
)


class TestReportValidator:  # UC-13.1 | PLAN-4
    """Tests for ReportValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a ReportValidator instance."""
        return ReportValidator()

    def test_init_with_default_schema(self):
        """Test initialization with default schema path."""
        validator = ReportValidator()
        assert validator.schema_path is not None
        assert validator.schema_path.name == "schema.json"

    def test_init_with_custom_schema(self, temp_dir: Path):
        """Test initialization with custom schema path."""
        schema_path = temp_dir / "custom-schema.json"
        schema_path.write_text('{"type": "object"}')

        validator = ReportValidator(schema_path=schema_path)
        assert validator.schema_path == schema_path

    def test_schema_property_loads_schema(self, validator):
        """Test that schema property loads the schema."""
        schema = validator.schema
        assert isinstance(schema, dict)
        assert "type" in schema

    def test_validate_valid_report(self, validator, valid_report_data):
        """Test validation of valid report data."""
        is_valid, errors = validator.validate(valid_report_data)

        assert is_valid is True
        assert errors == []

    def test_validate_minimal_report(self, validator, minimal_report_data):
        """Test validation of minimal valid report."""
        is_valid, errors = validator.validate(minimal_report_data)

        assert is_valid is True
        assert errors == []

    def test_validate_missing_metadata(self, validator):
        """Test validation catches missing metadata."""
        data = {
            "summary": {
                "total_commits": 0,
                "total_prs_opened": 0,
                "total_prs_merged": 0,
                "total_issues_opened": 0,
                "total_issues_closed": 0,
                "repos_contributed_to": 0
            },
            "activity": {
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "reviews": [],
                "comments": [],
                "repositories": []
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        assert any("metadata" in e.lower() for e in errors)

    def test_validate_missing_summary(self, validator):
        """Test validation catches missing summary."""
        data = {
            "metadata": {
                "generated_at": "2024-12-31T00:00:00Z",
                "user": {"login": "testuser"},
                "period": {
                    "type": "monthly",
                    "year": 2024,
                    "start_date": "2024-12-01",
                    "end_date": "2024-12-31"
                },
                "schema_version": "1.0"
            },
            "activity": {
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "reviews": [],
                "comments": [],
                "repositories": []
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        assert any("summary" in e.lower() for e in errors)

    def test_validate_missing_activity(self, validator):
        """Test validation catches missing activity."""
        data = {
            "metadata": {
                "generated_at": "2024-12-31T00:00:00Z",
                "user": {"login": "testuser"},
                "period": {
                    "type": "monthly",
                    "year": 2024,
                    "start_date": "2024-12-01",
                    "end_date": "2024-12-31"
                },
                "schema_version": "1.0"
            },
            "summary": {
                "total_commits": 0,
                "total_prs_opened": 0,
                "total_prs_merged": 0,
                "total_issues_opened": 0,
                "total_issues_closed": 0,
                "repos_contributed_to": 0
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        assert any("activity" in e.lower() for e in errors)

    def test_validate_missing_user_login(self, validator):
        """Test validation catches missing user.login."""
        data = {
            "metadata": {
                "generated_at": "2024-12-31T00:00:00Z",
                "user": {},  # Missing login
                "period": {
                    "type": "monthly",
                    "year": 2024,
                    "start_date": "2024-12-01",
                    "end_date": "2024-12-31"
                },
                "schema_version": "1.0"
            },
            "summary": {
                "total_commits": 0,
                "total_prs_opened": 0,
                "total_prs_merged": 0,
                "total_issues_opened": 0,
                "total_issues_closed": 0,
                "repos_contributed_to": 0
            },
            "activity": {
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "reviews": [],
                "comments": [],
                "repositories": []
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        assert any("login" in e.lower() for e in errors)

    def test_validate_invalid_period_type(self, validator):
        """Test validation catches invalid period type."""
        data = {
            "metadata": {
                "generated_at": "2024-12-31T00:00:00Z",
                "user": {"login": "testuser"},
                "period": {
                    "type": "weekly",  # Invalid
                    "year": 2024,
                    "start_date": "2024-12-01",
                    "end_date": "2024-12-31"
                },
                "schema_version": "1.0"
            },
            "summary": {
                "total_commits": 0,
                "total_prs_opened": 0,
                "total_prs_merged": 0,
                "total_issues_opened": 0,
                "total_issues_closed": 0,
                "repos_contributed_to": 0
            },
            "activity": {
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "reviews": [],
                "comments": [],
                "repositories": []
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False

    def test_validate_invalid_data_type(self, validator):
        """Test validation catches invalid data types."""
        data = {
            "metadata": {
                "generated_at": "2024-12-31T00:00:00Z",
                "user": {"login": "testuser"},
                "period": {
                    "type": "monthly",
                    "year": "2024",  # Should be integer
                    "start_date": "2024-12-01",
                    "end_date": "2024-12-31"
                },
                "schema_version": "1.0"
            },
            "summary": {
                "total_commits": "five",  # Should be integer
                "total_prs_opened": 0,
                "total_prs_merged": 0,
                "total_issues_opened": 0,
                "total_issues_closed": 0,
                "repos_contributed_to": 0
            },
            "activity": {
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "reviews": [],
                "comments": [],
                "repositories": []
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is False

    def test_validate_with_metrics(self, validator, valid_report_data):
        """Test validation with metrics section."""
        data = valid_report_data.copy()
        data["metrics"] = {
            "pr_metrics": {
                "avg_commits_per_pr": 2.5,
                "avg_time_to_merge_hours": 24.0
            }
        }

        is_valid, errors = validator.validate(data)

        assert is_valid is True


class TestValidateFile:  # UC-13.1 | PLAN-4
    """Tests for validate_file method."""

    def test_validate_file_success(self, temp_dir: Path, valid_report_data):
        """Test validating a valid JSON file."""
        file_path = temp_dir / "report.json"
        file_path.write_text(json.dumps(valid_report_data))

        validator = ReportValidator()
        is_valid, errors = validator.validate_file(file_path)

        assert is_valid is True
        assert errors == []

    def test_validate_file_not_found(self, temp_dir: Path):
        """Test error for non-existent file."""
        validator = ReportValidator()
        is_valid, errors = validator.validate_file(temp_dir / "nonexistent.json")

        assert is_valid is False
        assert any("not found" in e.lower() for e in errors)

    def test_validate_file_not_json_extension(self, temp_dir: Path):
        """Test error for non-JSON file."""
        file_path = temp_dir / "report.txt"
        file_path.write_text("{}")

        validator = ReportValidator()
        is_valid, errors = validator.validate_file(file_path)

        assert is_valid is False
        assert any("json" in e.lower() for e in errors)

    def test_validate_file_invalid_json(self, temp_dir: Path):
        """Test error for invalid JSON content."""
        file_path = temp_dir / "report.json"
        file_path.write_text("not valid json {{{")

        validator = ReportValidator()
        is_valid, errors = validator.validate_file(file_path)

        assert is_valid is False
        assert any("invalid json" in e.lower() for e in errors)


class TestConvenienceFunctions:  # UC-13.1 | PLAN-4
    """Tests for convenience functions."""

    def test_validate_report_function(self, valid_report_data):
        """Test validate_report convenience function."""
        is_valid, errors = validate_report(valid_report_data)

        assert is_valid is True
        assert errors == []

    def test_validate_report_file_function(self, temp_dir: Path, valid_report_data):
        """Test validate_report_file convenience function."""
        file_path = temp_dir / "report.json"
        file_path.write_text(json.dumps(valid_report_data))

        is_valid, errors = validate_report_file(file_path)

        assert is_valid is True
        assert errors == []


class TestErrorMessages:  # UC-13.1 | PLAN-4
    """Tests for error message formatting."""

    def test_error_message_includes_path(self):
        """Test that error messages include field path."""
        validator = ReportValidator()
        data = {"metadata": {}}  # Missing required fields

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        # Check for path-like information in errors
        assert len(errors) > 0

    def test_error_message_is_human_readable(self):
        """Test that error messages are human-readable."""
        validator = ReportValidator()
        data = {"something": "wrong"}

        is_valid, errors = validator.validate(data)

        assert is_valid is False
        # All errors should be strings
        assert all(isinstance(e, str) for e in errors)
        # No error should be empty
        assert all(len(e) > 0 for e in errors)
