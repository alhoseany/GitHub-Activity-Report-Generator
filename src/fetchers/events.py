# =============================================================================
# FILE: src/fetchers/events.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Events Fetcher.

This module fetches user events from the GitHub Events API:
- Endpoint: /users/{username}/events
- Returns: Push events, PR events, Issue events, Comment events, etc.
- Limitation: Only returns last 90 days of events

Event types captured:
- PushEvent: Code pushes
- PullRequestEvent: PR opened/closed/merged
- IssueEvent: Issue opened/closed
- IssueCommentEvent: Comments on issues
- PullRequestReviewCommentEvent: PR review comments
- CreateEvent: Branch/tag creation
- DeleteEvent: Branch/tag deletion
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class EventsFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch user events from GitHub Events API."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize events fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to fetch events for
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
        Fetch events for a date range.

        Note: Events API returns all recent events, so we fetch all
        and filter by date range.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Events within the date range
        """
        try:
            events = self.gh.api(
                f"/users/{self.username}/events",
                paginate=True
            )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch events: {e}")
            return []

        # Ensure events is a list
        if not isinstance(events, list):
            events = [events] if events else []

        # Filter by date range
        filtered: list[dict[str, Any]] = []
        for event in events:
            event_date_str = event.get("created_at", "")[:10]
            if event_date_str:
                try:
                    if start.isoformat() <= event_date_str <= end.isoformat():
                        filtered.append(event)
                except (ValueError, TypeError):
                    continue

        return filtered

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for an event."""
        return event.get("id")

    def filter_by_type(
        self,
        events: list[dict[str, Any]],
        event_types: list[str]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Filter events by type.

        Args:
            events: List of events
            event_types: Event types to include (e.g., ["PushEvent", "PullRequestEvent"])

        Returns:
            list[dict]: Filtered events
        """
        return [e for e in events if e.get("type") in event_types]

    def extract_push_events(
        self,
        events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Extract PushEvent data.

        Args:
            events: List of events

        Returns:
            list[dict]: Push event data with commits
        """
        push_events = self.filter_by_type(events, ["PushEvent"])
        result: list[dict[str, Any]] = []

        for event in push_events:
            payload = event.get("payload", {})
            repo = event.get("repo", {})
            commits = payload.get("commits", [])

            for commit in commits:
                result.append({
                    "sha": commit.get("sha"),
                    "message": commit.get("message", ""),
                    "repository": repo.get("name", ""),
                    "date": event.get("created_at"),
                    "url": commit.get("url", ""),
                    "author": commit.get("author", {}).get("name", ""),
                })

        return result

    def extract_pr_events(
        self,
        events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Extract PullRequestEvent data.

        Args:
            events: List of events

        Returns:
            list[dict]: PR event data
        """
        pr_events = self.filter_by_type(events, ["PullRequestEvent"])
        result: list[dict[str, Any]] = []

        for event in pr_events:
            payload = event.get("payload", {})
            pr = payload.get("pull_request", {})
            repo = event.get("repo", {})

            result.append({
                "number": pr.get("number"),
                "title": pr.get("title", ""),
                "state": pr.get("state", ""),
                "action": payload.get("action", ""),
                "repository": repo.get("name", ""),
                "created_at": pr.get("created_at"),
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
                "url": pr.get("html_url", ""),
            })

        return result

    def extract_issue_events(
        self,
        events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Extract IssuesEvent data.

        Args:
            events: List of events

        Returns:
            list[dict]: Issue event data
        """
        issue_events = self.filter_by_type(events, ["IssuesEvent"])
        result: list[dict[str, Any]] = []

        for event in issue_events:
            payload = event.get("payload", {})
            issue = payload.get("issue", {})
            repo = event.get("repo", {})

            result.append({
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "state": issue.get("state", ""),
                "action": payload.get("action", ""),
                "repository": repo.get("name", ""),
                "created_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "url": issue.get("html_url", ""),
                "labels": [l.get("name", "") for l in issue.get("labels", [])],
            })

        return result

    def extract_comment_events(
        self,
        events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Extract comment events (IssueCommentEvent, PullRequestReviewCommentEvent).

        Args:
            events: List of events

        Returns:
            list[dict]: Comment event data
        """
        comment_events = self.filter_by_type(
            events,
            ["IssueCommentEvent", "PullRequestReviewCommentEvent"]
        )
        result: list[dict[str, Any]] = []

        for event in comment_events:
            payload = event.get("payload", {})
            comment = payload.get("comment", {})
            repo = event.get("repo", {})
            issue = payload.get("issue", {})

            result.append({
                "type": event.get("type"),
                "repository": repo.get("name", ""),
                "issue_number": issue.get("number"),
                "created_at": comment.get("created_at") or event.get("created_at"),
                "body_length": len(comment.get("body", "")),
                "url": comment.get("html_url", ""),
            })

        return result
