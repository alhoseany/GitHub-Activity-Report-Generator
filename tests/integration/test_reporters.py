# =============================================================================
# FILE: tests/integration/test_reporters.py
# TASKS: UC-13.2
# PLAN: Section 4
# =============================================================================
"""
Integration tests for report generation.  # UC-13.2 | PLAN-4

Tests reporter classes for JSON and Markdown output generation.

Tests:
- JsonReporter output generation
- MarkdownReporter output generation
- Report file writing
- Report schema validation
"""
import pytest
import json
from datetime import date
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.reporters.json_report import JsonReporter
from src.reporters.markdown_report import MarkdownReporter
from src.reporters.validator import ReportValidator
from src.processors.aggregator import AggregatedData


class TestJsonReporter:  # UC-13.2 | PLAN-4
    """Integration tests for JsonReporter."""

    @pytest.fixture
    def reporter(self, temp_reports_dir: Path):
        """Create a JsonReporter instance."""
        return JsonReporter(output_dir=str(temp_reports_dir), include_links=True)

    @pytest.fixture
    def sample_aggregated_data(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Create sample AggregatedData."""
        return AggregatedData(
            commits=sample_commits[:2] if sample_commits else [],
            pull_requests=sample_pull_requests[:2] if sample_pull_requests else [],
            issues=sample_issues[:2] if sample_issues else [],
            reviews=sample_reviews[:2] if sample_reviews else [],
            comments=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["testorg/test-repo", "testorg/another-repo"]
        )

    def test_build_report_returns_dict(self, reporter, sample_aggregated_data):
        """Test that build_report returns a dictionary."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert isinstance(result, dict)

    def test_report_has_required_sections(self, reporter, sample_aggregated_data):
        """Test that report has required sections."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert "metadata" in result
        assert "summary" in result
        assert "activity" in result

    def test_report_metadata_structure(self, reporter, sample_aggregated_data):
        """Test metadata section structure."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        metadata = result["metadata"]
        assert "generated_at" in metadata
        assert "user" in metadata
        assert "period" in metadata
        assert "schema_version" in metadata

    def test_report_validates_against_schema(self, reporter, sample_aggregated_data):
        """Test that generated report validates against schema."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        validator = ReportValidator()
        is_valid, errors = validator.validate(result)

        assert is_valid, f"Validation errors: {errors}"

    def test_generate_creates_file(self, reporter, sample_aggregated_data):
        """Test that generate creates a file."""
        file_path = reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert file_path.exists()
        assert file_path.suffix == ".json"

    def test_generated_file_is_valid_json(self, reporter, sample_aggregated_data):
        """Test that generated file is valid JSON."""
        file_path = reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        # Should not raise
        with open(file_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert "metadata" in loaded
        assert "summary" in loaded
        assert "activity" in loaded


class TestMarkdownReporter:  # UC-13.2 | PLAN-4
    """Integration tests for MarkdownReporter."""

    @pytest.fixture
    def reporter(self, temp_reports_dir: Path):
        """Create a MarkdownReporter instance."""
        return MarkdownReporter(output_dir=str(temp_reports_dir), include_links=True)

    @pytest.fixture
    def sample_aggregated_data(self, sample_commits, sample_pull_requests, sample_issues, sample_reviews):
        """Create sample AggregatedData."""
        return AggregatedData(
            commits=sample_commits[:2] if sample_commits else [],
            pull_requests=sample_pull_requests[:2] if sample_pull_requests else [],
            issues=sample_issues[:2] if sample_issues else [],
            reviews=sample_reviews[:2] if sample_reviews else [],
            comments=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["testorg/test-repo", "testorg/another-repo"]
        )

    def test_build_report_returns_string(self, reporter, sample_aggregated_data):
        """Test that build_report returns a string."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert isinstance(result, str)

    def test_report_has_title(self, reporter, sample_aggregated_data):
        """Test that markdown report has a title."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert "#" in result  # Has headers

    def test_report_has_summary_section(self, reporter, sample_aggregated_data):
        """Test that markdown report has summary section."""
        result = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        # Should contain summary information
        assert "summary" in result.lower() or "commits" in result.lower()

    def test_generate_creates_file(self, reporter, sample_aggregated_data):
        """Test that generate creates a file."""
        file_path = reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert file_path.exists()
        assert file_path.suffix == ".md"

    def test_generated_file_content(self, reporter, sample_aggregated_data):
        """Test that generated file has correct content."""
        file_path = reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        content = file_path.read_text()
        assert "#" in content  # Has markdown headers
        assert "testuser" in content  # Has username


class TestReporterIntegration:  # UC-13.2 | PLAN-4
    """Test reporter integration scenarios."""

    @pytest.fixture
    def sample_aggregated_data(self):
        """Create sample AggregatedData with realistic data."""
        return AggregatedData(
            commits=[
                {"sha": "abc123", "message": "Fix bug", "repository": "org/repo", "date": "2024-12-15T10:00:00Z"},
            ],
            pull_requests=[
                {"number": 42, "title": "New feature", "repository": "org/repo", "state": "merged",
                 "created_at": "2024-12-15T11:00:00Z", "merged_at": "2024-12-16T11:00:00Z"},
            ],
            issues=[
                {"number": 100, "title": "Bug report", "repository": "org/repo", "state": "open",
                 "created_at": "2024-12-15T12:00:00Z"},
            ],
            reviews=[],
            comments=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"]
        )

    def test_json_and_markdown_together(self, sample_aggregated_data, temp_reports_dir: Path):
        """Test generating both JSON and Markdown reports."""
        json_reporter = JsonReporter(output_dir=str(temp_reports_dir))
        md_reporter = MarkdownReporter(output_dir=str(temp_reports_dir))

        json_path = json_reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        md_path = md_reporter.generate(
            data=sample_aggregated_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        assert json_path.exists()
        assert md_path.exists()

    def test_quarterly_report(self, sample_aggregated_data, temp_reports_dir: Path):
        """Test quarterly report generation."""
        reporter = JsonReporter(output_dir=str(temp_reports_dir))
        sample_aggregated_data.start_date = date(2024, 10, 1)
        sample_aggregated_data.end_date = date(2024, 12, 31)

        report = reporter.build_report(
            data=sample_aggregated_data,
            year=2024,
            period_type="quarterly",
            period_value=4
        )

        assert report["metadata"]["period"]["type"] == "quarterly"
        assert report["metadata"]["period"]["year"] == 2024

    def test_empty_data_report(self, temp_reports_dir: Path):
        """Test report generation with empty data."""
        reporter = JsonReporter(output_dir=str(temp_reports_dir))
        empty_data = AggregatedData(
            commits=[],
            pull_requests=[],
            issues=[],
            reviews=[],
            comments=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=[]
        )

        report = reporter.build_report(
            data=empty_data,
            year=2024,
            period_type="monthly",
            period_value=12
        )

        # Should still be valid
        validator = ReportValidator()
        is_valid, errors = validator.validate(report)
        assert is_valid, f"Validation errors: {errors}"

        # Summary should show zeros
        assert report["summary"]["total_commits"] == 0


class TestMarkdownReleaseSection:  # UC-13.2 | PLAN-4
    """Tests for release contributions in Markdown report."""

    def test_release_table_rendered(self, temp_reports_dir):
        """Release contributions table should appear in markdown."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[], reviews=[], comments=[],
            releases=[
                {
                    "tag_name": "1.0.0",
                    "name": "v1.0.0",
                    "repository": "org/repo",
                    "published_at": "2024-12-15T00:00:00Z",
                    "html_url": "https://github.com/org/repo/releases/tag/1.0.0",
                    "total_commits": 50,
                    "user_commits": 10,
                    "total_prs": 8,
                    "user_reviewed_prs": 3,
                    "contribution_weight": 27.0,
                    "is_monorepo_release": False,
                    "anomalies": [],
                    "detection_method": "github_releases",
                },
            ],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"],
        )

        reporter = MarkdownReporter(output_dir=str(temp_reports_dir), include_links=True)
        report = reporter.build_report(data, 2024, "monthly", 12, None)

        assert "## Release Contributions" in report
        assert "10/50" in report   # User/Total commits
        assert "3/8" in report     # User/Total PRs
        assert "27.0%" in report   # Contribution weight

    def test_zero_contribution_releases_filtered(self, temp_reports_dir):
        """Releases with no user contribution should not appear."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[], reviews=[], comments=[],
            releases=[
                {
                    "tag_name": "1.0.0",
                    "repository": "org/repo",
                    "user_commits": 0,
                    "user_reviewed_prs": 0,
                    "total_commits": 50,
                    "total_prs": 8,
                    "contribution_weight": 0.0,
                    "is_monorepo_release": False,
                    "anomalies": [],
                    "detection_method": "github_releases",
                    "name": "",
                    "published_at": "2024-12-15",
                    "html_url": "",
                },
            ],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"],
        )

        reporter = MarkdownReporter(output_dir=str(temp_reports_dir), include_links=True)
        report = reporter.build_report(data, 2024, "monthly", 12, None)

        assert "## Release Contributions" not in report


class TestMarkdownReviewLinks:  # UC-13.2 | PLAN-4
    """Tests for review PR links in Markdown report."""

    def test_reviews_have_pr_links(self, temp_reports_dir):
        """Reviews should link to the PR when include_links is enabled."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[],
            reviews=[
                {
                    "pr_number": 42,
                    "repository": "org/repo",
                    "state": "APPROVED",
                    "submitted_at": "2024-12-15T00:00:00Z",
                },
            ],
            comments=[], releases=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"],
        )

        reporter = MarkdownReporter(output_dir=str(temp_reports_dir), include_links=True)
        report = reporter.build_report(data, 2024, "monthly", 12, None)

        assert "https://github.com/org/repo/pull/42" in report
        assert "[org/repo#42]" in report

    def test_reviews_no_links_when_disabled(self, temp_reports_dir):
        """Reviews should not have links when include_links is disabled."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[],
            reviews=[
                {
                    "pr_number": 42,
                    "repository": "org/repo",
                    "state": "APPROVED",
                    "submitted_at": "2024-12-15T00:00:00Z",
                },
            ],
            comments=[], releases=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"],
        )

        reporter = MarkdownReporter(output_dir=str(temp_reports_dir), include_links=False)
        report = reporter.build_report(data, 2024, "monthly", 12, None)

        assert "https://github.com" not in report
        assert "- org/repo#42" in report


class TestJsonReleaseOutput:  # UC-13.2 | PLAN-4
    """Tests for release data in JSON report."""

    def test_json_releases_filtered(self, temp_reports_dir):
        """JSON activity.releases should only include contributed releases."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[], reviews=[], comments=[],
            releases=[
                {
                    "tag_name": "1.0",
                    "name": "",
                    "repository": "org/repo",
                    "published_at": "2024-12-15",
                    "html_url": "",
                    "total_commits": 10,
                    "user_commits": 5,
                    "total_prs": 2,
                    "user_reviewed_prs": 1,
                    "contribution_weight": 50.0,
                    "is_monorepo_release": False,
                    "anomalies": [],
                    "detection_method": "github_releases",
                },
                {
                    "tag_name": "2.0",
                    "name": "",
                    "repository": "org/repo",
                    "published_at": "2024-12-20",
                    "html_url": "",
                    "total_commits": 20,
                    "user_commits": 0,
                    "total_prs": 5,
                    "user_reviewed_prs": 0,
                    "contribution_weight": 0.0,
                    "is_monorepo_release": False,
                    "anomalies": [],
                    "detection_method": "github_releases",
                },
            ],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=["org/repo"],
        )

        reporter = JsonReporter(output_dir=str(temp_reports_dir), include_links=True)
        report = reporter.build_report(data, 2024, "monthly", 12, None)

        # Only the contributed release should be in activity
        assert len(report["activity"]["releases"]) == 1
        assert report["activity"]["releases"][0]["tag_name"] == "1.0"

    def test_json_release_metrics(self, temp_reports_dir):
        """Release metrics should appear when provided."""
        data = AggregatedData(
            commits=[], pull_requests=[], issues=[], reviews=[], comments=[], releases=[],
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            username="testuser",
            repositories=[],
        )

        metrics: dict[str, Any] = {
            "release_metrics": {
                "releases_contributed_to": 3,
                "total_releases_in_period": 5,
                "avg_contribution_weight": 35.0,
                "releases": [],
            }
        }

        reporter = JsonReporter(output_dir=str(temp_reports_dir), include_links=True)
        report = reporter.build_report(data, 2024, "monthly", 12, metrics)

        assert "release_metrics" in report["metrics"]
        assert report["metrics"]["release_metrics"]["releases_contributed_to"] == 3
