# =============================================================================
# FILE: src/fetchers/reviews.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Reviews Fetcher.

This module fetches PR reviews using the GitHub API:
- Endpoint: /repos/{owner}/{repo}/pulls/{number}/reviews
- Returns: Review ID, state, body, user, submitted date

Review states:
- APPROVED: Review approved the PR
- CHANGES_REQUESTED: Review requested changes
- COMMENTED: Review left comments without approval/rejection
- DISMISSED: Review was dismissed
- PENDING: Review is pending submission

Note: Reviews are fetched per-PR, not by date range.
Implementation requires list of PRs from PullRequestsFetcher.
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class ReviewsFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch PR reviews from GitHub API."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize reviews fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to filter reviews by
            logger: Optional logger instance
        """
        super().__init__(gh_client, config, logger)
        self.username = username

    def _fetch_range(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch reviews for a date range.

        Note: Reviews don't have a direct date-based search.
        This method returns an empty list; use fetch_reviews_for_prs instead.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Empty list (use fetch_reviews_for_prs)
        """
        # Reviews must be fetched per-PR
        return []

    def fetch_reviews_for_prs(
        self,
        prs: list[dict[str, Any]],
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch reviews for a list of PRs.

        Args:
            prs: List of PR dictionaries with repository and number
            start: Start date for filtering reviews
            end: End date for filtering reviews

        Returns:
            list[dict]: Reviews within the date range
        """
        all_reviews: list[dict[str, Any]] = []

        for pr in prs:
            repo = pr.get("repository", "")
            pr_number = pr.get("number")

            if not repo or not pr_number:
                continue

            reviews = self._fetch_pr_reviews(repo, pr_number)

            # Filter by date and user
            for review in reviews:
                submitted_at = review.get("submitted_at", "")[:10]
                review_user = review.get("user", {}).get("login", "")

                if not submitted_at:
                    continue

                # Check date range
                if start.isoformat() <= submitted_at <= end.isoformat():
                    # Check if user matches (for reviews user gave)
                    if review_user == self.username:
                        all_reviews.append({
                            "id": review.get("id"),
                            "pr_number": pr_number,
                            "repository": repo,
                            "state": review.get("state", ""),
                            "submitted_at": review.get("submitted_at"),
                            "body_length": len(review.get("body", "") or ""),
                            "user": review_user,
                        })

        return all_reviews

    def _fetch_pr_reviews(
        self,
        repo: str,
        pr_number: int
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch reviews for a single PR.

        Args:
            repo: Repository name (owner/repo)
            pr_number: Pull request number

        Returns:
            list[dict]: Reviews for the PR
        """
        try:
            reviews = self.gh.api(
                f"/repos/{repo}/pulls/{pr_number}/reviews",
                paginate=True
            )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch reviews for {repo}#{pr_number}: {e}")
            return []

        if not isinstance(reviews, list):
            reviews = [reviews] if reviews else []

        return reviews

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for a review."""
        return str(event.get("id", "")) if event.get("id") else None

    def normalize_review(
        self,
        review: dict[str, Any]
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Normalize review data to standard format.

        Args:
            review: Raw review data

        Returns:
            dict: Normalized review data
        """
        return {
            "id": review.get("id"),
            "pr_number": review.get("pr_number"),
            "repository": review.get("repository"),
            "state": review.get("state", ""),
            "submitted_at": review.get("submitted_at"),
            "body_length": len(review.get("body", "") or ""),
        }

    def count_by_state(
        self,
        reviews: list[dict[str, Any]]
    ) -> dict[str, int]:  # UC-2.2 | PLAN-3.4
        """
        Count reviews by state.

        Args:
            reviews: List of reviews

        Returns:
            dict: Count per state (APPROVED, CHANGES_REQUESTED, COMMENTED, etc.)
        """
        counts: dict[str, int] = {}
        for review in reviews:
            state = review.get("state", "UNKNOWN")
            counts[state] = counts.get(state, 0) + 1
        return counts

    def fetch_reviews_on_authored_prs(
        self,
        prs: list[dict[str, Any]],
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch reviews ON PRs authored by the user (from other reviewers).

        This is used to calculate metrics like "PRs with requested changes".

        Args:
            prs: List of PR dictionaries authored by the user
            start: Start date for filtering reviews
            end: End date for filtering reviews

        Returns:
            list[dict]: Reviews by others on the user's PRs
        """
        all_reviews: list[dict[str, Any]] = []

        for pr in prs:
            repo = pr.get("repository", "")
            pr_number = pr.get("number")

            if not repo or not pr_number:
                continue

            reviews = self._fetch_pr_reviews(repo, pr_number)

            # Filter by date but exclude the user's own reviews
            for review in reviews:
                submitted_at = review.get("submitted_at", "")[:10]
                review_user = review.get("user", {}).get("login", "")

                if not submitted_at:
                    continue

                # Check date range and exclude self-reviews
                if start.isoformat() <= submitted_at <= end.isoformat():
                    if review_user != self.username:
                        all_reviews.append({
                            "id": review.get("id"),
                            "pr_number": pr_number,
                            "repository": repo,
                            "state": review.get("state", ""),
                            "submitted_at": review.get("submitted_at"),
                            "body_length": len(review.get("body", "") or ""),
                            "user": review_user,
                        })

        return all_reviews
