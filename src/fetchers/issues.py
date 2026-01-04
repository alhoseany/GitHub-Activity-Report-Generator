# =============================================================================
# FILE: src/fetchers/issues.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Issues Fetcher.

This module fetches issues using the gh search command:
- Command: gh search issues author:{user} created:{start}..{end}
- Returns: Issue URL, title, state, dates, repository, etc.

Data captured:
- Issue number and URL
- Title and body
- State (open/closed)
- Created/updated/closed dates
- Repository (owner/repo)
- Labels
- Assignees
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING
from urllib.parse import quote

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class IssuesFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch issues using gh search."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize issues fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to fetch issues for
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
        Fetch issues for a date range.

        Uses GitHub Search API directly via gh api to avoid gh search issues
        with username validation.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Issues within the date range
        """
        # Use GitHub Search API directly via gh api
        # type:issue excludes PRs from results
        query = f"author:{self.username} type:issue created:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch issues: {e}")
            return []

        # Transform results to standard format
        issues: list[dict[str, Any]] = []
        for item in items:
            # Extract repository from url (format: https://api.github.com/repos/owner/repo/issues/123)
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""

            # Extract label names
            labels = item.get("labels", [])
            if isinstance(labels, list):
                label_names = [
                    l.get("name", "") if isinstance(l, dict) else str(l)
                    for l in labels
                ]
            else:
                label_names = []

            issues.append({
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "repository": repo_name,
                "created_at": item.get("created_at"),
                "closed_at": item.get("closed_at"),
                "url": item.get("html_url", ""),
                "labels": label_names,
            })

        return issues

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for an issue."""
        return event.get("url")

    def fetch_assigned_issues(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch issues assigned to the user (not authored).

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Assigned issues within the date range
        """
        # Use GitHub Search API directly
        query = f"assignee:{self.username} type:issue created:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch assigned issues: {e}")
            return []

        issues: list[dict[str, Any]] = []
        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""

            labels = item.get("labels", [])
            if isinstance(labels, list):
                label_names = [
                    l.get("name", "") if isinstance(l, dict) else str(l)
                    for l in labels
                ]
            else:
                label_names = []

            issues.append({
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "repository": repo_name,
                "created_at": item.get("created_at"),
                "closed_at": item.get("closed_at"),
                "url": item.get("html_url", ""),
                "labels": label_names,
            })

        return issues

    def normalize_issue(
        self,
        issue: dict[str, Any]
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Normalize issue data to standard format.

        Args:
            issue: Raw issue data

        Returns:
            dict: Normalized issue data
        """
        repo = issue.get("repository", {})

        labels = issue.get("labels", [])
        if isinstance(labels, list):
            label_names = [
                l.get("name", "") if isinstance(l, dict) else str(l)
                for l in labels
            ]
        else:
            label_names = []

        return {
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "state": issue.get("state", ""),
            "repository": repo.get("nameWithOwner", repo.get("full_name", "")),
            "created_at": issue.get("createdAt") or issue.get("created_at"),
            "closed_at": issue.get("closedAt") or issue.get("closed_at"),
            "url": issue.get("url", ""),
            "labels": label_names,
        }
