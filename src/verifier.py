# =============================================================================
# FILE: src/verifier.py
# TASKS: UC-14.1
# PLAN: Section 6
# =============================================================================
"""
Report Verification.

This module provides post-generation verification of report data
against the live GitHub API. It spot-checks a sample of items
to detect data integrity issues.

Checks performed:
- Internal consistency: summary counts match activity arrays
- Comment uniqueness: no duplicate URLs
- Commit spot-check: verify SHAs exist on GitHub
- PR state verification: verify all PR states match GitHub
- Review spot-check: verify review states match GitHub
- Issue verification: verify all issue states match GitHub
- Release spot-check: verify release data matches GitHub
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .processors.aggregator import AggregatedData
    from .utils.gh_client import GitHubClient


@dataclass
class CheckResult:
    """Result of a single verification check."""
    name: str
    passed: bool
    checked: int
    failed: int
    details: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Combined result of all verification checks."""
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Whether all checks passed."""
        return all(c.passed for c in self.checks)

    @property
    def failed_count(self) -> int:
        """Number of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "passed": self.passed,
            "total_checks": len(self.checks),
            "failed_checks": self.failed_count,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "checked": c.checked,
                    "failed": c.failed,
                    "details": c.details,
                }
                for c in self.checks
            ],
        }

    def summary(self) -> str:
        """Generate a human-readable summary of all checks."""
        lines: list[str] = []
        status = "PASSED" if self.passed else "FAILED"
        passed_count = len(self.checks) - self.failed_count
        lines.append(
            f"Verification: {status} ({passed_count}/{len(self.checks)} checks passed)"
        )
        for check in self.checks:
            icon = "\u2713" if check.passed else "\u2717"
            items_passed = check.checked - check.failed
            lines.append(
                f"  {icon} {check.name}: {items_passed}/{check.checked} passed"
            )
            for detail in check.details:
                lines.append(f"    - {detail}")
        return "\n".join(lines)


class ReportVerifier:  # UC-14.1 | PLAN-6
    """
    Verify report data against the live GitHub API.

    Runs a series of checks to validate data integrity:
    internal consistency, comment uniqueness, and spot-checks
    of commits, PRs, reviews, issues, and releases against
    the GitHub API.
    """

    def __init__(
        self,
        gh_client: "GitHubClient",
        logger: Any = None,
        sample_size: int = 5,
    ):
        """
        Initialize verifier.

        Args:
            gh_client: GitHubClient instance for API calls
            logger: Optional logger instance
            sample_size: Number of items to spot-check (default: 5)
        """
        self.gh = gh_client
        self.logger = logger
        self.sample_size = sample_size

    def verify(self, data: "AggregatedData") -> VerificationResult:
        """
        Run all verification checks against aggregated data.

        Args:
            data: AggregatedData to verify

        Returns:
            VerificationResult: Combined results of all checks
        """
        result = VerificationResult()

        result.checks.append(self._verify_internal_consistency(data))
        result.checks.append(self._verify_comment_uniqueness(data.comments))

        if data.commits:
            result.checks.append(self._spot_check_commits(data.commits))
        if data.pull_requests:
            result.checks.append(self._verify_pr_states(data.pull_requests))
        if data.reviews:
            result.checks.append(self._spot_check_reviews(data.reviews))
        if data.issues:
            result.checks.append(self._verify_issues(data.issues))
        if data.releases:
            result.checks.append(self._spot_check_releases(data.releases))

        return result

    def _log_info(self, message: str) -> None:
        """Log an info message if logger is available."""
        if self.logger:
            self.logger.info(message)

    def _log_warning(self, message: str) -> None:
        """Log a warning message if logger is available."""
        if self.logger:
            self.logger.warning(message)

    def _verify_internal_consistency(
        self, data: "AggregatedData"
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Verify internal consistency of aggregated data.

        Checks that property-based counts match the actual
        list lengths, and that summary dict values are consistent.

        Args:
            data: AggregatedData to check

        Returns:
            CheckResult: Result of consistency checks
        """
        self._log_info("Checking internal consistency...")
        details: list[str] = []
        checks_run = 0
        failures = 0

        # Check property counts match list lengths
        consistency_checks: list[tuple[str, int, int]] = [
            ("commits", len(data.commits), data.total_commits),
            ("pull_requests", len(data.pull_requests), data.total_prs_opened),
            ("issues", len(data.issues), data.total_issues_opened),
            ("comments", len(data.comments), data.total_comments),
        ]

        for name, actual_len, property_val in consistency_checks:
            checks_run += 1
            if actual_len != property_val:
                failures += 1
                details.append(
                    f"{name}: list length ({actual_len}) != "
                    f"property value ({property_val})"
                )

        # Check summary dict values match properties
        summary = data.get_summary()
        summary_checks: list[tuple[str, str, int]] = [
            ("total_commits", "total_commits", data.total_commits),
            ("total_prs_opened", "total_prs_opened", data.total_prs_opened),
            ("total_issues_opened", "total_issues_opened", data.total_issues_opened),
            ("total_comments", "total_comments", data.total_comments),
            ("total_prs_merged", "total_prs_merged", data.total_prs_merged),
            ("total_prs_reviewed", "total_prs_reviewed", data.total_prs_reviewed),
            ("total_issues_closed", "total_issues_closed", data.total_issues_closed),
            ("repos_contributed_to", "repos_contributed_to", data.repos_contributed_to),
        ]

        for summary_key, _label, expected in summary_checks:
            checks_run += 1
            actual = summary.get(summary_key)
            if actual != expected:
                failures += 1
                details.append(
                    f"summary[{summary_key}] ({actual}) != "
                    f"property ({expected})"
                )

        return CheckResult(
            name="internal_consistency",
            passed=failures == 0,
            checked=checks_run,
            failed=failures,
            details=details,
        )

    def _verify_comment_uniqueness(
        self, comments: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Verify that there are no duplicate comment URLs.

        Args:
            comments: List of comment dicts

        Returns:
            CheckResult: Result of uniqueness check
        """
        self._log_info("Checking comment uniqueness...")
        details: list[str] = []
        url_counts: Counter[str] = Counter()

        for comment in comments:
            url = comment.get("url", "")
            if url:
                url_counts[url] += 1

        duplicates = {url: count for url, count in url_counts.items() if count > 1}

        for url, count in duplicates.items():
            details.append(f"Duplicate comment URL ({count}x): {url}")

        return CheckResult(
            name="comment_uniqueness",
            passed=len(duplicates) == 0,
            checked=len(comments),
            failed=len(duplicates),
            details=details,
        )

    def _spot_check_commits(
        self, commits: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Spot-check that commit SHAs exist on GitHub.

        Samples up to sample_size commits and verifies each
        exists via the API.

        Args:
            commits: List of commit dicts with 'sha' and 'repository' keys

        Returns:
            CheckResult: Result of commit spot-check
        """
        sample = random.sample(commits, min(self.sample_size, len(commits)))
        self._log_info(f"Spot-checking {len(sample)} commits...")
        details: list[str] = []
        failures = 0

        for commit in sample:
            sha = commit.get("sha", "")
            repo = commit.get("repository", "")
            if not sha or not repo:
                failures += 1
                details.append(f"Commit missing sha or repository: {commit}")
                continue

            try:
                self.gh.api(f"/repos/{repo}/commits/{sha}")
            except Exception as e:
                failures += 1
                details.append(f"Commit {sha[:8]} not found in {repo}: {e}")

        return CheckResult(
            name="commit_spot_check",
            passed=failures == 0,
            checked=len(sample),
            failed=failures,
            details=details,
        )

    def _verify_pr_states(
        self, pull_requests: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Verify PR states match the live GitHub API.

        Checks all PRs (not sampled, as PR counts are typically small).
        Handles the merged state: GitHub returns state="closed" for
        merged PRs, but the report may store state as "merged" when
        merged_at is set.

        Args:
            pull_requests: List of PR dicts

        Returns:
            CheckResult: Result of PR state verification
        """
        self._log_info(f"Verifying {len(pull_requests)} PR states...")
        details: list[str] = []
        failures = 0

        for pr in pull_requests:
            repo = pr.get("repository", "")
            number = pr.get("number")
            local_state = pr.get("state", "")
            if not repo or not number:
                failures += 1
                details.append(f"PR missing repository or number: {pr}")
                continue

            try:
                api_pr = self.gh.api(f"/repos/{repo}/pulls/{number}")
                api_state = api_pr.get("state", "") if isinstance(api_pr, dict) else ""
                api_merged_at = api_pr.get("merged_at") if isinstance(api_pr, dict) else None

                # Normalize states for comparison:
                # GitHub API returns "open" or "closed" for state.
                # A merged PR has state="closed" and merged_at set.
                # Reports may store "merged" as the state.
                if api_merged_at and local_state == "merged":
                    # Report says merged, API confirms merged_at is set: OK
                    continue
                if api_merged_at and local_state == "closed":
                    # Report says closed, but it was actually merged: mismatch
                    failures += 1
                    details.append(
                        f"PR {repo}#{number}: report says '{local_state}' "
                        f"but PR was merged (merged_at={api_merged_at})"
                    )
                    continue

                if api_state != local_state:
                    # If local says "merged" but API says "closed" with no merged_at,
                    # that's a real mismatch
                    failures += 1
                    details.append(
                        f"PR {repo}#{number}: report says '{local_state}' "
                        f"but API says '{api_state}'"
                    )
            except Exception as e:
                failures += 1
                details.append(f"PR {repo}#{number} API error: {e}")

        return CheckResult(
            name="pr_state_verification",
            passed=failures == 0,
            checked=len(pull_requests),
            failed=failures,
            details=details,
        )

    def _spot_check_reviews(
        self, reviews: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Spot-check review states against the GitHub API.

        Samples up to sample_size reviews and verifies each
        review's state matches the API.

        Args:
            reviews: List of review dicts

        Returns:
            CheckResult: Result of review spot-check
        """
        sample = random.sample(reviews, min(self.sample_size, len(reviews)))
        self._log_info(f"Spot-checking {len(sample)} reviews...")
        details: list[str] = []
        failures = 0

        for review in sample:
            repo = review.get("repository", "")
            pr_number = review.get("pr_number")
            local_state = review.get("state", "")
            review_user = review.get("user", "")
            if not repo or not pr_number:
                failures += 1
                details.append(f"Review missing repository or pr_number: {review}")
                continue

            try:
                api_reviews = self.gh.api(
                    f"/repos/{repo}/pulls/{pr_number}/reviews"
                )
                if not isinstance(api_reviews, list):
                    api_reviews = []

                # Find the matching review by user
                matched = False
                for api_review in api_reviews:
                    api_user = api_review.get("user", {})
                    api_login = api_user.get("login", "") if isinstance(api_user, dict) else ""
                    if api_login == review_user:
                        api_state = api_review.get("state", "")
                        if api_state.upper() != local_state.upper():
                            failures += 1
                            details.append(
                                f"Review on {repo}#{pr_number} by {review_user}: "
                                f"report says '{local_state}' but API says '{api_state}'"
                            )
                        matched = True
                        break

                if not matched and review_user:
                    failures += 1
                    details.append(
                        f"Review by {review_user} on {repo}#{pr_number} "
                        f"not found in API response"
                    )
            except Exception as e:
                failures += 1
                details.append(
                    f"Review on {repo}#{pr_number} API error: {e}"
                )

        return CheckResult(
            name="review_spot_check",
            passed=failures == 0,
            checked=len(sample),
            failed=failures,
            details=details,
        )

    def _verify_issues(
        self, issues: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Verify issue states match the live GitHub API.

        Checks all issues (not sampled, as issue counts are
        typically small).

        Args:
            issues: List of issue dicts

        Returns:
            CheckResult: Result of issue state verification
        """
        self._log_info(f"Verifying {len(issues)} issue states...")
        details: list[str] = []
        failures = 0

        for issue in issues:
            repo = issue.get("repository", "")
            number = issue.get("number")
            local_state = issue.get("state", "")
            if not repo or not number:
                failures += 1
                details.append(f"Issue missing repository or number: {issue}")
                continue

            try:
                api_issue = self.gh.api(f"/repos/{repo}/issues/{number}")
                api_state = (
                    api_issue.get("state", "") if isinstance(api_issue, dict) else ""
                )

                if api_state != local_state:
                    failures += 1
                    details.append(
                        f"Issue {repo}#{number}: report says '{local_state}' "
                        f"but API says '{api_state}'"
                    )
            except Exception as e:
                failures += 1
                details.append(f"Issue {repo}#{number} API error: {e}")

        return CheckResult(
            name="issue_state_verification",
            passed=failures == 0,
            checked=len(issues),
            failed=failures,
            details=details,
        )

    def _spot_check_releases(
        self, releases: list[dict[str, Any]]
    ) -> CheckResult:  # UC-14.1 | PLAN-6
        """
        Spot-check that releases exist on GitHub.

        Samples up to sample_size releases and verifies each
        exists via the API. Falls back to checking the tag ref
        if the release endpoint returns an error.

        Args:
            releases: List of release dicts

        Returns:
            CheckResult: Result of release spot-check
        """
        sample = random.sample(releases, min(self.sample_size, len(releases)))
        self._log_info(f"Spot-checking {len(sample)} releases...")
        details: list[str] = []
        failures = 0

        for release in sample:
            repo = release.get("repository", "")
            tag_name = release.get("tag_name", "")
            if not repo or not tag_name:
                failures += 1
                details.append(
                    f"Release missing repository or tag_name: {release}"
                )
                continue

            try:
                self.gh.api(f"/repos/{repo}/releases/tags/{tag_name}")
            except Exception:
                # Fall back to checking the tag ref directly
                try:
                    self.gh.api(f"/repos/{repo}/git/ref/tags/{tag_name}")
                except Exception as e:
                    failures += 1
                    details.append(
                        f"Release {tag_name} in {repo} not found: {e}"
                    )

        return CheckResult(
            name="release_spot_check",
            passed=failures == 0,
            checked=len(sample),
            failed=failures,
            details=details,
        )
