# =============================================================================
# FILE: src/fetchers/comments.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Comments Fetcher.

This module fetches comments using the GitHub Search API:
- Issue comments: gh api /search/issues?q=commenter:{user}
- PR review comments: gh api /repos/{owner}/{repo}/pulls/comments

Data captured:
- Comment ID and URL
- Body text
- Created/updated dates
- Repository
- Issue/PR number
- Comment type (issue_comment, review_comment)
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING
from urllib.parse import quote

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class CommentsFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch comments using GitHub API."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize comments fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to fetch comments for
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
        Fetch comments for a date range.

        Uses GitHub Search API to find issues/PRs where user commented.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Comments within the date range
        """
        all_comments: list[dict[str, Any]] = []

        # Fetch issue comments via search
        issue_comments = self._fetch_issue_comments(start, end)
        all_comments.extend(issue_comments)

        return all_comments

    def _fetch_issue_comments(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch issue/PR comments by the user in the date range.

        Uses the commenter: search qualifier to find issues/PRs
        where the user commented, then fetches the actual comments.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Issue comments within the date range
        """
        # Search for issues/PRs where user commented in date range
        # Note: GitHub search doesn't have created filter for comments,
        # so we search by updated issues and filter comments by date
        query = f"commenter:{self.username} updated:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint, paginate=True)
            if isinstance(result, dict):
                items = result.get("items", [])
            elif isinstance(result, list):
                # Paginated results come as list
                items = []
                for page in result:
                    if isinstance(page, dict):
                        items.extend(page.get("items", []))
                    elif isinstance(page, list):
                        items.extend(page)
            else:
                items = []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch commented issues: {e}")
            return []

        # For each issue/PR, fetch the user's comments
        comments: list[dict[str, Any]] = []
        seen_comment_ids: set[int] = set()

        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""
            issue_number = item.get("number")

            if not repo_name or not issue_number:
                continue

            # Fetch comments on this issue/PR
            issue_comments = self._fetch_comments_on_issue(
                repo_name, issue_number, start, end, seen_comment_ids
            )
            comments.extend(issue_comments)

        return comments

    def _fetch_comments_on_issue(
        self,
        repo: str,
        issue_number: int,
        start: date,
        end: date,
        seen_ids: set[int]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch comments by user on a specific issue/PR.

        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue or PR number
            start: Start date for filtering
            end: End date for filtering
            seen_ids: Set of already seen comment IDs

        Returns:
            list[dict]: Comments by the user on this issue
        """
        comments: list[dict[str, Any]] = []
        start_str = start.isoformat()
        end_str = end.isoformat()

        try:
            # Fetch issue comments
            issue_comments = self.gh.api(
                f"/repos/{repo}/issues/{issue_number}/comments",
                paginate=True
            )
            if not isinstance(issue_comments, list):
                issue_comments = [issue_comments] if issue_comments else []

            for comment in issue_comments:
                comment_id = comment.get("id")
                if comment_id in seen_ids:
                    continue

                # Check if comment is by this user
                user = comment.get("user", {}) or {}
                if user.get("login") != self.username:
                    continue

                # Check if comment is in date range
                created_at = comment.get("created_at", "")[:10]
                if not (start_str <= created_at <= end_str):
                    continue

                seen_ids.add(comment_id)
                comments.append({
                    "id": comment_id,
                    "type": "issue_comment",
                    "body": comment.get("body", ""),
                    "repository": repo,
                    "issue_number": issue_number,
                    "created_at": comment.get("created_at"),
                    "updated_at": comment.get("updated_at"),
                    "url": comment.get("html_url", ""),
                })

        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to fetch comments for {repo}#{issue_number}: {e}")

        return comments

    def fetch_review_comments(
        self,
        prs: list[dict[str, Any]],
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch PR review comments (inline code comments) by the user.

        Args:
            prs: List of PR dictionaries to check
            start: Start date
            end: End date

        Returns:
            list[dict]: Review comments within the date range
        """
        comments: list[dict[str, Any]] = []
        seen_ids: set[int] = set()
        start_str = start.isoformat()
        end_str = end.isoformat()

        for pr in prs:
            repo = pr.get("repository", "")
            pr_number = pr.get("number")

            if not repo or not pr_number:
                continue

            try:
                review_comments = self.gh.api(
                    f"/repos/{repo}/pulls/{pr_number}/comments",
                    paginate=True
                )
                if not isinstance(review_comments, list):
                    review_comments = [review_comments] if review_comments else []

                for comment in review_comments:
                    comment_id = comment.get("id")
                    if comment_id in seen_ids:
                        continue

                    # Check if comment is by this user
                    user = comment.get("user", {}) or {}
                    if user.get("login") != self.username:
                        continue

                    # Check if comment is in date range
                    created_at = comment.get("created_at", "")[:10]
                    if not (start_str <= created_at <= end_str):
                        continue

                    seen_ids.add(comment_id)
                    comments.append({
                        "id": comment_id,
                        "type": "review_comment",
                        "body": comment.get("body", ""),
                        "repository": repo,
                        "pr_number": pr_number,
                        "created_at": comment.get("created_at"),
                        "updated_at": comment.get("updated_at"),
                        "url": comment.get("html_url", ""),
                        "path": comment.get("path", ""),
                        "line": comment.get("line"),
                    })

            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to fetch review comments for {repo}#{pr_number}: {e}")

        return comments

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for a comment."""
        return str(event.get("id")) if event.get("id") else event.get("url")
