# =============================================================================
# FILE: src/reporters/validator.py
# TASKS: UC-12.1
# PLAN: Section 3.11
# =============================================================================
"""
Report Schema Validator.  # UC-12.1 | PLAN-3.11

This module validates JSON reports against the schema:
- Loads schema from src/config/schema.json
- Validates report structure using jsonschema library
- Returns validation errors with helpful messages

Classes:
- ReportValidator: Main validator class with validate() and validate_file() methods

Functions:
- validate_report(report_data): Convenience function for validation
  Returns: tuple[bool, list[str]] - (is_valid, error_messages)

Validation checks:
- Required sections: metadata, summary, activity
- Metadata fields: generated_at, user, period, schema_version
- Summary fields: total_commits, total_prs_opened, total_prs_merged, etc.
- Activity fields: commits[], pull_requests[], issues[], reviews[], comments[], repositories[]
- Optional metrics section
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError, SchemaError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class ReportValidator:  # UC-12.1 | PLAN-3.11
    """
    Validate reports against JSON schema.

    Uses the jsonschema library for comprehensive validation.
    Falls back to basic validation if jsonschema is not installed.

    Attributes:
        schema_path: Path to the JSON schema file

    Example:
        >>> validator = ReportValidator()
        >>> is_valid, errors = validator.validate(report_data)
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """

    def __init__(self, schema_path: str | Path | None = None):
        """
        Initialize validator.  # UC-12.1 | PLAN-3.11

        Args:
            schema_path: Path to JSON schema file. If None, uses default location.
        """
        if schema_path is None:
            # Default schema location
            schema_path = Path(__file__).parent.parent / "config" / "schema.json"

        self.schema_path = Path(schema_path)
        self._schema: dict[str, Any] | None = None

    @property
    def schema(self) -> dict[str, Any]:  # UC-12.1 | PLAN-3.11
        """
        Load and cache schema.

        Returns:
            dict: The JSON schema dictionary
        """
        if self._schema is None:
            if self.schema_path.exists():
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    self._schema = json.load(f)
            else:
                # Minimal fallback schema
                self._schema = self._get_fallback_schema()
        return self._schema

    def _get_fallback_schema(self) -> dict[str, Any]:  # UC-12.1 | PLAN-3.11
        """Get minimal fallback schema if main schema is not available."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["metadata", "summary", "activity"],
            "properties": {
                "metadata": {
                    "type": "object",
                    "required": ["generated_at", "user", "period", "schema_version"],
                    "properties": {
                        "generated_at": {"type": "string"},
                        "user": {
                            "type": "object",
                            "required": ["login"],
                            "properties": {"login": {"type": "string"}}
                        },
                        "period": {
                            "type": "object",
                            "required": ["type", "year", "start_date", "end_date"],
                            "properties": {
                                "type": {"type": "string", "enum": ["monthly", "quarterly"]},
                                "year": {"type": "integer"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"}
                            }
                        },
                        "schema_version": {"type": "string"}
                    }
                },
                "summary": {
                    "type": "object",
                    "required": ["total_commits", "total_prs_opened", "total_prs_merged",
                                "total_issues_opened", "total_issues_closed", "repos_contributed_to"]
                },
                "activity": {
                    "type": "object",
                    "required": ["commits", "pull_requests", "issues", "reviews", "comments", "repositories"],
                    "properties": {
                        "commits": {"type": "array"},
                        "pull_requests": {"type": "array"},
                        "issues": {"type": "array"},
                        "reviews": {"type": "array"},
                        "comments": {"type": "array"},
                        "repositories": {"type": "array"}
                    }
                },
                "metrics": {"type": "object"}
            }
        }

    def validate(
        self,
        report_data: dict[str, Any]
    ) -> tuple[bool, list[str]]:  # UC-12.1 | PLAN-3.11
        """
        Validate report against schema.

        Args:
            report_data: Report dictionary to validate

        Returns:
            tuple[bool, list[str]]: (is_valid, list of error messages)

        Example:
            >>> validator = ReportValidator()
            >>> is_valid, errors = validator.validate({"metadata": {}, "summary": {}})
            >>> print(is_valid)  # False - missing required fields
        """
        errors: list[str] = []

        if HAS_JSONSCHEMA:
            errors = self._validate_with_jsonschema(report_data)
        else:
            errors = self._validate_basic(report_data)

        return (len(errors) == 0, errors)

    def validate_file(
        self,
        file_path: str | Path
    ) -> tuple[bool, list[str]]:  # UC-12.1 | PLAN-3.11
        """
        Validate a saved report file.

        Args:
            file_path: Path to the JSON report file

        Returns:
            tuple[bool, list[str]]: (is_valid, list of error messages)

        Example:
            >>> validator = ReportValidator()
            >>> is_valid, errors = validator.validate_file("reports/2024/2024-12-github-activity-1.json")
        """
        file_path = Path(file_path)
        errors: list[str] = []

        if not file_path.exists():
            return (False, [f"File not found: {file_path}"])

        if not file_path.suffix.lower() == ".json":
            return (False, [f"File must be a JSON file: {file_path}"])

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except json.JSONDecodeError as e:
            return (False, [f"Invalid JSON: {e}"])
        except IOError as e:
            return (False, [f"Could not read file: {e}"])

        return self.validate(report_data)

    def _validate_with_jsonschema(
        self,
        report_data: dict[str, Any]
    ) -> list[str]:  # UC-12.1 | PLAN-3.11
        """
        Validate using jsonschema library.

        Provides detailed error messages with path information.
        """
        errors: list[str] = []

        try:
            # Use Draft7Validator for better error messages
            validator = Draft7Validator(self.schema)

            # Collect all errors, not just the first one
            for error in sorted(validator.iter_errors(report_data), key=lambda e: str(e.path)):
                # Build helpful error message
                path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
                message = self._format_error_message(error, path)
                errors.append(message)

        except SchemaError as e:
            errors.append(f"Schema error: {e.message}")

        return errors

    def _format_error_message(
        self,
        error: ValidationError,
        path: str
    ) -> str:  # UC-12.1 | PLAN-3.11
        """
        Format a validation error into a helpful message.

        Args:
            error: The ValidationError from jsonschema
            path: The path to the error location

        Returns:
            str: A human-readable error message
        """
        # Handle common error types with specific messages
        if error.validator == "required":
            missing = error.validator_value if isinstance(error.validator_value, list) else [error.validator_value]
            if len(missing) == 1:
                return f"Missing required field '{missing[0]}' at {path}"
            return f"Missing required fields {missing} at {path}"

        if error.validator == "type":
            expected = error.validator_value
            actual = type(error.instance).__name__
            return f"Type error at {path}: expected {expected}, got {actual}"

        if error.validator == "enum":
            allowed = error.validator_value
            return f"Invalid value at {path}: must be one of {allowed}"

        if error.validator == "minimum":
            return f"Value at {path} must be >= {error.validator_value}"

        if error.validator == "maximum":
            return f"Value at {path} must be <= {error.validator_value}"

        if error.validator == "minLength":
            return f"String at {path} must have at least {error.validator_value} characters"

        if error.validator == "pattern":
            return f"Value at {path} does not match required pattern"

        # Default message
        return f"Validation error at {path}: {error.message}"

    def _validate_basic(
        self,
        report_data: dict[str, Any]
    ) -> list[str]:  # UC-12.1 | PLAN-3.11
        """
        Basic validation without jsonschema library.

        Checks required fields and basic types.
        """
        errors: list[str] = []

        # Check top-level type
        if not isinstance(report_data, dict):
            errors.append("Report must be an object")
            return errors

        # Check required top-level fields
        required_fields = ["metadata", "summary", "activity"]
        for field in required_fields:
            if field not in report_data:
                errors.append(f"Missing required field: {field}")

        # Validate metadata
        if "metadata" in report_data:
            errors.extend(self._validate_metadata(report_data["metadata"]))

        # Validate summary
        if "summary" in report_data:
            errors.extend(self._validate_summary(report_data["summary"]))

        # Validate activity
        if "activity" in report_data:
            errors.extend(self._validate_activity(report_data["activity"]))

        # Validate metrics (optional)
        if "metrics" in report_data:
            if not isinstance(report_data["metrics"], dict):
                errors.append("metrics must be an object")

        return errors

    def _validate_metadata(
        self,
        metadata: Any
    ) -> list[str]:  # UC-12.1 | PLAN-3.11
        """Validate metadata section."""
        errors: list[str] = []

        if not isinstance(metadata, dict):
            errors.append("metadata must be an object")
            return errors

        # Required metadata fields
        required = ["generated_at", "user", "period", "schema_version"]
        for field in required:
            if field not in metadata:
                errors.append(f"metadata.{field} is required")

        # Validate user
        if "user" in metadata:
            user = metadata["user"]
            if not isinstance(user, dict):
                errors.append("metadata.user must be an object")
            elif "login" not in user:
                errors.append("metadata.user.login is required")

        # Validate period
        if "period" in metadata:
            period = metadata["period"]
            if not isinstance(period, dict):
                errors.append("metadata.period must be an object")
            else:
                period_required = ["type", "year", "start_date", "end_date"]
                for field in period_required:
                    if field not in period:
                        errors.append(f"metadata.period.{field} is required")

                if "type" in period and period["type"] not in ["monthly", "quarterly"]:
                    errors.append("metadata.period.type must be 'monthly' or 'quarterly'")

        return errors

    def _validate_summary(
        self,
        summary: Any
    ) -> list[str]:  # UC-12.1 | PLAN-3.11
        """Validate summary section."""
        errors: list[str] = []

        if not isinstance(summary, dict):
            errors.append("summary must be an object")
            return errors

        # Required summary fields
        required = [
            "total_commits", "total_prs_opened", "total_prs_merged",
            "total_issues_opened", "total_issues_closed", "repos_contributed_to"
        ]
        for field in required:
            if field not in summary:
                errors.append(f"summary.{field} is required")
            elif not isinstance(summary.get(field), int):
                errors.append(f"summary.{field} must be an integer")

        return errors

    def _validate_activity(
        self,
        activity: Any
    ) -> list[str]:  # UC-12.1 | PLAN-3.11
        """Validate activity section."""
        errors: list[str] = []

        if not isinstance(activity, dict):
            errors.append("activity must be an object")
            return errors

        # Required activity arrays
        required_arrays = [
            "commits", "pull_requests", "issues",
            "reviews", "comments", "repositories"
        ]
        for field in required_arrays:
            if field not in activity:
                errors.append(f"activity.{field} is required")
            elif not isinstance(activity.get(field), list):
                errors.append(f"activity.{field} must be an array")

        return errors


def validate_report(
    report_data: dict[str, Any],
    schema_path: str | Path | None = None
) -> tuple[bool, list[str]]:  # UC-12.1 | PLAN-3.11
    """
    Convenience function to validate a report.

    Args:
        report_data: Report dictionary to validate
        schema_path: Optional path to schema file

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)

    Example:
        >>> from src.reporters.validator import validate_report
        >>> is_valid, errors = validate_report(report_data)
        >>> if not is_valid:
        ...     print("Validation failed:", errors)
    """
    validator = ReportValidator(schema_path)
    return validator.validate(report_data)


def validate_report_file(
    file_path: str | Path,
    schema_path: str | Path | None = None
) -> tuple[bool, list[str]]:  # UC-12.1 | PLAN-3.11
    """
    Convenience function to validate a report file.

    Args:
        file_path: Path to the JSON report file
        schema_path: Optional path to schema file

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)

    Example:
        >>> from src.reporters.validator import validate_report_file
        >>> is_valid, errors = validate_report_file("reports/2024/report.json")
    """
    validator = ReportValidator(schema_path)
    return validator.validate_file(file_path)
