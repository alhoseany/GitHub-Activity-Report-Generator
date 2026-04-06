# =============================================================================
# FILE: tests/unit/test_verifier.py
# TASKS: UC-14.1
# PLAN: Section 6
# =============================================================================
"""
Unit tests for the ReportVerifier module.  # UC-14.1 | PLAN-6

Tests:
- CheckResult dataclass defaults and properties
- VerificationResult passed/failed logic and serialization
- Internal consistency checks against AggregatedData
- Comment uniqueness detection
- Commit spot-check via mocked gh_client
- PR state verification including merged-state normalization
- Issue state verification
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.verifier import CheckResult, ReportVerifier, VerificationResult
from src.processors.aggregator import AggregatedData


# =============================================================================
# Helpers
# =============================================================================

def _make_verifier(sample_size: int = 5) -> tuple[ReportVerifier, MagicMock]:
    """Return a ReportVerifier wired to a fresh MagicMock gh_client."""
    mock_client = MagicMock()
    verifier = ReportVerifier(gh_client=mock_client, logger=None, sample_size=sample_size)
    return verifier, mock_client


def _simple_data(
    commits: list | None = None,
    pull_requests: list | None = None,
    issues: list | None = None,
    reviews: list | None = None,
    comments: list | None = None,
    repositories: list | None = None,
) -> AggregatedData:
    """Build a minimal AggregatedData with sensible defaults."""
    return AggregatedData(
        commits=commits or [],
        pull_requests=pull_requests or [],
        issues=issues or [],
        reviews=reviews or [],
        comments=comments or [],
        releases=[],
        repositories=repositories or [],
    )


# =============================================================================
# TestCheckResult
# =============================================================================

class TestCheckResult:
    """Tests for the CheckResult dataclass."""

    def test_check_result_defaults(self):
        """Default values are set correctly when no details list is provided."""
        result = CheckResult(name="sample_check", passed=True, checked=3, failed=0)

        assert result.name == "sample_check"
        assert result.passed is True
        assert result.checked == 3
        assert result.failed == 0
        assert result.details == []

    def test_check_result_passed_when_failed_is_zero(self):
        """passed=True correlates with failed=0 (no automatic derivation, just storage)."""
        result = CheckResult(name="check", passed=True, checked=10, failed=0)

        assert result.passed is True
        assert result.failed == 0

    def test_check_result_failed_stores_details(self):
        """Details list is stored correctly when provided."""
        details = ["item A mismatch", "item B missing"]
        result = CheckResult(
            name="check", passed=False, checked=2, failed=2, details=details
        )

        assert result.passed is False
        assert result.failed == 2
        assert result.details == details


# =============================================================================
# TestVerificationResult
# =============================================================================

class TestVerificationResult:
    """Tests for the VerificationResult dataclass."""

    def test_all_passed(self):
        """passed property is True when every check passed."""
        result = VerificationResult(checks=[
            CheckResult(name="a", passed=True, checked=5, failed=0),
            CheckResult(name="b", passed=True, checked=3, failed=0),
        ])

        assert result.passed is True
        assert result.failed_count == 0

    def test_some_failed(self):
        """passed property is False when at least one check failed."""
        result = VerificationResult(checks=[
            CheckResult(name="a", passed=True, checked=5, failed=0),
            CheckResult(name="b", passed=False, checked=3, failed=2),
        ])

        assert result.passed is False
        assert result.failed_count == 1

    def test_empty_checks_passes(self):
        """An empty checks list is treated as passed (vacuously true)."""
        result = VerificationResult()

        assert result.passed is True
        assert result.failed_count == 0

    def test_to_dict(self):
        """to_dict serialization contains all required keys and correct values."""
        checks = [
            CheckResult(name="consistency", passed=True, checked=8, failed=0),
            CheckResult(name="uniqueness", passed=False, checked=4, failed=1,
                        details=["dup: http://example.com"]),
        ]
        result = VerificationResult(checks=checks)

        d = result.to_dict()

        assert d["passed"] is False
        assert d["total_checks"] == 2
        assert d["failed_checks"] == 1
        assert len(d["checks"]) == 2

        consistency = d["checks"][0]
        assert consistency["name"] == "consistency"
        assert consistency["passed"] is True
        assert consistency["checked"] == 8
        assert consistency["failed"] == 0
        assert consistency["details"] == []

        uniqueness = d["checks"][1]
        assert uniqueness["name"] == "uniqueness"
        assert uniqueness["passed"] is False
        assert uniqueness["details"] == ["dup: http://example.com"]

    def test_summary_format(self):
        """summary() contains the overall status and per-check lines."""
        result = VerificationResult(checks=[
            CheckResult(name="internal_consistency", passed=True, checked=12, failed=0),
            CheckResult(name="comment_uniqueness", passed=False, checked=5, failed=2,
                        details=["Dup: http://x.com/1"]),
        ])

        summary = result.summary()

        assert "FAILED" in summary
        assert "internal_consistency" in summary
        assert "comment_uniqueness" in summary
        # Passed check count formatted as items_passed/checked
        assert "12/12" in summary
        # Details appear indented
        assert "Dup: http://x.com/1" in summary

    def test_summary_all_passed(self):
        """summary() shows PASSED when all checks pass."""
        result = VerificationResult(checks=[
            CheckResult(name="check_a", passed=True, checked=3, failed=0),
        ])

        assert "PASSED" in result.summary()


# =============================================================================
# TestInternalConsistency
# =============================================================================

class TestInternalConsistency:
    """Tests for ReportVerifier._verify_internal_consistency."""

    def test_consistent_data_passes(self):
        """Valid AggregatedData whose counts all align produces a passing check."""
        data = _simple_data(
            commits=[{"sha": "a1"}, {"sha": "a2"}],
            pull_requests=[{"number": 1}, {"number": 2}],
            issues=[{"number": 10, "state": "open"}],
            comments=[{"url": "http://example.com/c1"}],
            repositories=["org/repo"],
        )
        verifier, _ = _make_verifier()

        check = verifier._verify_internal_consistency(data)

        assert check.name == "internal_consistency"
        assert check.passed is True
        assert check.failed == 0

    def test_inconsistent_summary_fails(self):
        """When the summary dict returns a value mismatched with properties, the check fails.

        We achieve this by creating a subclass that overrides get_summary() to
        return stale / wrong values.
        """

        class MismatchedData(AggregatedData):
            def get_summary(self) -> dict[str, Any]:
                base = super().get_summary()
                # Inject a wrong value for total_commits
                base["total_commits"] = self.total_commits + 99
                return base

        data = MismatchedData(
            commits=[{"sha": "x"}],
            repositories=["org/repo"],
        )

        verifier, _ = _make_verifier()
        check = verifier._verify_internal_consistency(data)

        assert check.passed is False
        assert check.failed >= 1
        assert any("total_commits" in d for d in check.details)


# =============================================================================
# TestCommentUniqueness
# =============================================================================

class TestCommentUniqueness:
    """Tests for ReportVerifier._verify_comment_uniqueness."""

    def test_unique_comments_passes(self):
        """All distinct URLs produce a passing uniqueness check."""
        comments = [
            {"url": "http://github.com/comment/1"},
            {"url": "http://github.com/comment/2"},
            {"url": "http://github.com/comment/3"},
        ]
        verifier, _ = _make_verifier()

        check = verifier._verify_comment_uniqueness(comments)

        assert check.name == "comment_uniqueness"
        assert check.passed is True
        assert check.failed == 0
        assert check.checked == 3

    def test_duplicate_comments_fails(self):
        """Repeated URLs are flagged and the check fails."""
        dup_url = "http://github.com/comment/42"
        comments = [
            {"url": dup_url},
            {"url": "http://github.com/comment/1"},
            {"url": dup_url},
        ]
        verifier, _ = _make_verifier()

        check = verifier._verify_comment_uniqueness(comments)

        assert check.passed is False
        assert check.failed == 1
        assert any(dup_url in d for d in check.details)

    def test_empty_comments_passes(self):
        """An empty comment list produces a clean uniqueness check."""
        verifier, _ = _make_verifier()

        check = verifier._verify_comment_uniqueness([])

        assert check.passed is True
        assert check.checked == 0
        assert check.failed == 0

    def test_comments_without_url_are_ignored(self):
        """Comments that have no 'url' key do not trigger false duplicate flags."""
        comments = [
            {"id": 1},  # no url
            {"id": 2},  # no url
        ]
        verifier, _ = _make_verifier()

        check = verifier._verify_comment_uniqueness(comments)

        assert check.passed is True
        assert check.failed == 0


# =============================================================================
# TestSpotCheckCommits
# =============================================================================

class TestSpotCheckCommits:
    """Tests for ReportVerifier._spot_check_commits."""

    def test_valid_commits_pass(self):
        """When the API returns a commit dict, the check passes."""
        commits = [{"sha": "abc123", "repository": "org/repo"}]
        verifier, mock_client = _make_verifier(sample_size=5)
        mock_client.api.return_value = {"sha": "abc123", "commit": {"message": "init"}}

        check = verifier._spot_check_commits(commits)

        assert check.name == "commit_spot_check"
        assert check.passed is True
        assert check.failed == 0
        assert check.checked == 1
        mock_client.api.assert_called_once_with("/repos/org/repo/commits/abc123")

    def test_missing_commit_fails(self):
        """When the API raises an exception, the commit is flagged as failed."""
        commits = [{"sha": "deadbeef", "repository": "org/repo"}]
        verifier, mock_client = _make_verifier(sample_size=5)
        mock_client.api.side_effect = Exception("404 Not Found")

        check = verifier._spot_check_commits(commits)

        assert check.passed is False
        assert check.failed == 1
        assert any("deadbeef" in d for d in check.details)

    def test_commit_missing_sha_fails(self):
        """A commit dict without 'sha' is counted as a failure."""
        commits = [{"repository": "org/repo"}]  # no sha
        verifier, _ = _make_verifier()

        check = verifier._spot_check_commits(commits)

        assert check.passed is False
        assert check.failed == 1

    def test_commit_missing_repo_fails(self):
        """A commit dict without 'repository' is counted as a failure."""
        commits = [{"sha": "abc123"}]  # no repository
        verifier, _ = _make_verifier()

        check = verifier._spot_check_commits(commits)

        assert check.passed is False
        assert check.failed == 1

    def test_multiple_commits_sampled(self):
        """Only up to sample_size commits are checked."""
        commits = [{"sha": f"sha{i}", "repository": "org/repo"} for i in range(20)]
        verifier, mock_client = _make_verifier(sample_size=3)
        mock_client.api.return_value = {"sha": "..."}

        check = verifier._spot_check_commits(commits)

        assert check.checked == 3
        assert mock_client.api.call_count == 3


# =============================================================================
# TestVerifyPrStates
# =============================================================================

class TestVerifyPrStates:
    """Tests for ReportVerifier._verify_pr_states."""

    def test_matching_pr_states_pass(self):
        """When API state matches local state, no failure is recorded."""
        prs = [{"number": 1, "repository": "org/repo", "state": "open"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {"state": "open", "merged_at": None}

        check = verifier._verify_pr_states(prs)

        assert check.name == "pr_state_verification"
        assert check.passed is True
        assert check.failed == 0
        assert check.checked == 1

    def test_merged_pr_state_handling(self):
        """Report state='merged' + API merged_at set → should pass (not a mismatch)."""
        prs = [{"number": 7, "repository": "org/repo", "state": "merged"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {
            "state": "closed",
            "merged_at": "2024-12-20T10:00:00Z",
        }

        check = verifier._verify_pr_states(prs)

        assert check.passed is True
        assert check.failed == 0

    def test_closed_pr_was_actually_merged_fails(self):
        """Report says 'closed' but API has merged_at set → mismatch, should fail."""
        prs = [{"number": 8, "repository": "org/repo", "state": "closed"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {
            "state": "closed",
            "merged_at": "2024-12-21T10:00:00Z",
        }

        check = verifier._verify_pr_states(prs)

        assert check.passed is False
        assert check.failed == 1
        assert any("merged" in d for d in check.details)

    def test_mismatched_state_fails(self):
        """When API state differs from local state and no merged_at, check fails."""
        prs = [{"number": 3, "repository": "org/repo", "state": "open"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {"state": "closed", "merged_at": None}

        check = verifier._verify_pr_states(prs)

        assert check.passed is False
        assert check.failed == 1
        assert any("org/repo#3" in d for d in check.details)

    def test_pr_api_error_fails(self):
        """An API exception on a PR is recorded as a failure."""
        prs = [{"number": 5, "repository": "org/repo", "state": "open"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.side_effect = Exception("Network error")

        check = verifier._verify_pr_states(prs)

        assert check.passed is False
        assert check.failed == 1

    def test_pr_missing_repo_fails(self):
        """A PR without 'repository' is recorded as a failure immediately."""
        prs = [{"number": 9, "state": "open"}]  # no repository
        verifier, _ = _make_verifier()

        check = verifier._verify_pr_states(prs)

        assert check.passed is False
        assert check.failed == 1


# =============================================================================
# TestVerifyIssues
# =============================================================================

class TestVerifyIssues:
    """Tests for ReportVerifier._verify_issues."""

    def test_matching_issue_states_pass(self):
        """When API state matches local state, the check passes."""
        issues = [{"number": 10, "repository": "org/repo", "state": "open"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {"state": "open"}

        check = verifier._verify_issues(issues)

        assert check.name == "issue_state_verification"
        assert check.passed is True
        assert check.failed == 0
        assert check.checked == 1
        mock_client.api.assert_called_once_with("/repos/org/repo/issues/10")

    def test_mismatched_issue_state_fails(self):
        """When API state differs from local state, the check fails with details."""
        issues = [{"number": 20, "repository": "org/repo", "state": "open"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.return_value = {"state": "closed"}

        check = verifier._verify_issues(issues)

        assert check.passed is False
        assert check.failed == 1
        assert any("org/repo#20" in d for d in check.details)
        assert any("open" in d for d in check.details)
        assert any("closed" in d for d in check.details)

    def test_issue_api_error_fails(self):
        """An API exception on an issue is recorded as a failure."""
        issues = [{"number": 30, "repository": "org/repo", "state": "closed"}]
        verifier, mock_client = _make_verifier()
        mock_client.api.side_effect = RuntimeError("timeout")

        check = verifier._verify_issues(issues)

        assert check.passed is False
        assert check.failed == 1

    def test_issue_missing_number_fails(self):
        """An issue without 'number' is recorded as a failure."""
        issues = [{"repository": "org/repo", "state": "open"}]  # no number
        verifier, _ = _make_verifier()

        check = verifier._verify_issues(issues)

        assert check.passed is False
        assert check.failed == 1

    def test_multiple_issues_all_match(self):
        """All issues passing state verification → single passing check."""
        issues = [
            {"number": 1, "repository": "org/repo", "state": "open"},
            {"number": 2, "repository": "org/repo", "state": "closed"},
        ]
        verifier, mock_client = _make_verifier()

        def api_side_effect(path: str) -> dict:
            if path.endswith("/1"):
                return {"state": "open"}
            return {"state": "closed"}

        mock_client.api.side_effect = api_side_effect

        check = verifier._verify_issues(issues)

        assert check.passed is True
        assert check.checked == 2
        assert check.failed == 0
