# =============================================================================
# FILE: src/fetchers/commits.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Commits Fetcher.

This module fetches commits using the gh search command:
- Command: gh search commits author:{user} committer-date:{start}..{end}
- Returns: Commit SHA, message, repository, date, etc.
- Advantage: Not limited to 90 days like Events API

Data captured:
- Commit SHA
- Commit message
- Repository (owner/repo)
- Author date
- Committer date
- URL
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING
from urllib.parse import quote

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class CommitsFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch commits using gh search."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize commits fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to fetch commits for
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
        Fetch commits for a date range.

        Uses gh api to search commits with author and date filters.
        Note: gh search commits requires search text, so we use the API instead.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Commits within the date range
        """
        # Use GitHub Search API directly via gh api
        # This allows qualifier-only searches unlike gh search commits
        query = f"author:{self.username} committer-date:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/commits?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch commits: {e}")
            return []

        # Transform results to standard format
        commits: list[dict[str, Any]] = []
        for item in items:
            commit_data = item.get("commit", {})
            repo = item.get("repository", {})

            commits.append({
                "sha": item.get("sha"),
                "message": commit_data.get("message", ""),
                "repository": repo.get("full_name", ""),
                "date": commit_data.get("committer", {}).get("date"),
                "author_date": commit_data.get("author", {}).get("date"),
                "url": item.get("html_url", ""),
            })

        return commits

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for a commit."""
        return event.get("sha") or event.get("url")

    def normalize_commit(
        self,
        commit: dict[str, Any]
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Normalize commit data to standard format.

        Args:
            commit: Raw commit data

        Returns:
            dict: Normalized commit data
        """
        commit_data = commit.get("commit", {})
        repo = commit.get("repository", {})

        return {
            "sha": commit.get("sha"),
            "message": commit_data.get("message", ""),
            "repository": repo.get("fullName", repo.get("full_name", "")),
            "date": commit_data.get("committer", {}).get("date"),
            "url": commit.get("url", ""),
            "additions": commit.get("additions", 0),
            "deletions": commit.get("deletions", 0),
        }
