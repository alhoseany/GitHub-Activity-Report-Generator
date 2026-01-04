# =============================================================================
# FILE: src/fetchers/pull_requests.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Pull Requests Fetcher.

This module fetches pull requests using the gh search command:
- Command: gh search prs author:{user} created:{start}..{end}
- Returns: PR URL, title, state, dates, repository, etc.

Data captured:
- PR number and URL
- Title and body
- State (open/closed/merged)
- Created/updated/merged dates
- Repository (owner/repo)
- Review status
- Merge status
"""
from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING
from urllib.parse import quote

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class PullRequestsFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch pull requests using gh search."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize pull requests fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to fetch PRs for
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
        Fetch pull requests for a date range.

        Uses GitHub Search API directly via gh api.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: PRs within the date range
        """
        # Use GitHub Search API directly via gh api
        # type:pr filters for pull requests only
        query = f"author:{self.username} type:pr created:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch PRs: {e}")
            return []

        # Transform results to standard format
        prs: list[dict[str, Any]] = []
        for item in items:
            # Extract repository from url
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""

            # Check if merged via pull_request field
            pr_data = item.get("pull_request", {})
            merged_at = pr_data.get("merged_at") if pr_data else None
            state = item.get("state", "")
            if merged_at:
                state = "merged"

            prs.append({
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": state,
                "repository": repo_name,
                "created_at": item.get("created_at"),
                "merged_at": merged_at,
                "closed_at": item.get("closed_at"),
                "url": item.get("html_url", ""),
            })

        return prs

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for a PR."""
        return event.get("url")

    def fetch_reviewed_prs(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch PRs reviewed by the user (not authored).

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: PRs reviewed within the date range
        """
        # Use GitHub Search API directly via gh api
        query = f"reviewed-by:{self.username} type:pr created:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch reviewed PRs: {e}")
            return []

        prs: list[dict[str, Any]] = []
        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""

            pr_data = item.get("pull_request", {})
            merged_at = pr_data.get("merged_at") if pr_data else None
            state = item.get("state", "")
            if merged_at:
                state = "merged"

            prs.append({
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": state,
                "repository": repo_name,
                "created_at": item.get("created_at"),
                "merged_at": merged_at,
                "closed_at": item.get("closed_at"),
                "url": item.get("html_url", ""),
            })

        return prs

    def normalize_pr(
        self,
        pr: dict[str, Any]
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Normalize PR data to standard format.

        Args:
            pr: Raw PR data

        Returns:
            dict: Normalized PR data
        """
        repo = pr.get("repository", {})

        return {
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "repository": repo.get("nameWithOwner", repo.get("full_name", "")),
            "created_at": pr.get("createdAt") or pr.get("created_at"),
            "merged_at": pr.get("mergedAt") or pr.get("merged_at"),
            "closed_at": pr.get("closedAt") or pr.get("closed_at"),
            "url": pr.get("url", ""),
            "commits_count": pr.get("commits_count", 0),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
        }

    def enrich_with_details(
        self,
        prs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Enrich PRs with additional details from the PR API.

        Fetches commits count, additions, deletions for each PR.

        Args:
            prs: List of PR dictionaries

        Returns:
            list[dict]: PRs enriched with additional details
        """
        enriched: list[dict[str, Any]] = []

        for pr in prs:
            repo = pr.get("repository", "")
            number = pr.get("number")

            if not repo or not number:
                enriched.append(pr)
                continue

            try:
                details = self.gh.api(f"/repos/{repo}/pulls/{number}")
                if isinstance(details, dict):
                    pr["commits_count"] = details.get("commits", 0)
                    pr["additions"] = details.get("additions", 0)
                    pr["deletions"] = details.get("deletions", 0)
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to fetch PR details for {repo}#{number}: {e}")

            enriched.append(pr)

        return enriched

    def fetch_prs_updated_in_period(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch PRs by the user that were updated in the period.

        This catches PRs created earlier but with activity (commits, comments)
        during the reporting period.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: PRs updated within the date range
        """
        # Search for PRs by the user that were updated in the period
        query = f"author:{self.username} type:pr updated:{start.isoformat()}..{end.isoformat()}"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch updated PRs: {e}")
            return []

        prs: list[dict[str, Any]] = []
        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""

            pr_data = item.get("pull_request", {})
            merged_at = pr_data.get("merged_at") if pr_data else None
            state = item.get("state", "")
            if merged_at:
                state = "merged"

            prs.append({
                "number": item.get("number"),
                "title": item.get("title", ""),
                "state": state,
                "repository": repo_name,
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "merged_at": merged_at,
                "closed_at": item.get("closed_at"),
                "url": item.get("html_url", ""),
            })

        return prs

    def fetch_commits_from_prs(
        self,
        prs: list[dict[str, Any]],
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch commits from PRs that fall within the date range.

        This fetches commits directly from PR branches, including unmerged PRs
        that wouldn't appear in the commit search.

        Args:
            prs: List of PR dictionaries
            start: Start date for filtering commits
            end: End date for filtering commits

        Returns:
            list[dict]: Commits from PRs within the date range
        """
        all_commits: list[dict[str, Any]] = []
        seen_shas: set[str] = set()

        for pr in prs:
            repo = pr.get("repository", "")
            number = pr.get("number")

            if not repo or not number:
                continue

            try:
                commits = self.gh.api(
                    f"/repos/{repo}/pulls/{number}/commits",
                    paginate=True
                )
                if not isinstance(commits, list):
                    commits = [commits] if commits else []

                for commit in commits:
                    sha = commit.get("sha", "")
                    if sha in seen_shas:
                        continue

                    # Check if commit author matches and date is in range
                    commit_data = commit.get("commit", {})
                    author_info = commit.get("author", {}) or {}
                    author_login = author_info.get("login", "")

                    # Also check commit.author for cases where GitHub user isn't linked
                    commit_author = commit_data.get("author", {})
                    committer = commit_data.get("committer", {})
                    commit_date_str = committer.get("date", "")[:10]

                    # Only include commits by this user within the date range
                    if author_login != self.username:
                        continue

                    if not (start.isoformat() <= commit_date_str <= end.isoformat()):
                        continue

                    seen_shas.add(sha)
                    all_commits.append({
                        "sha": sha,
                        "message": commit_data.get("message", ""),
                        "repository": repo,
                        "date": committer.get("date"),
                        "author_date": commit_author.get("date"),
                        "url": commit.get("html_url", ""),
                        "from_pr": number,  # Track which PR this commit came from
                    })

            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to fetch commits for {repo}#{number}: {e}")

        return all_commits

    def fetch_open_prs_with_activity(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch open PRs by the user that have activity in the period.

        GitHub's updated_at only shows the latest update time, not historical.
        This method fetches all open PRs and checks for reviews/comments in period.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Open PRs with activity in the date range
        """
        # First, get all open PRs by the user
        query = f"author:{self.username} type:pr is:open"
        encoded_query = quote(query, safe='')
        endpoint = f"/search/issues?q={encoded_query}&per_page=100"

        try:
            result = self.gh.api(endpoint)
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to fetch open PRs: {e}")
            return []

        prs_with_activity: list[dict[str, Any]] = []

        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = "/".join(repo_url.split("/")[-2:]) if repo_url else ""
            pr_number = item.get("number")

            if not repo_name or not pr_number:
                continue

            # Check if this PR has activity in the period
            has_activity = self._check_pr_activity_in_period(
                repo_name, pr_number, start, end
            )

            if has_activity:
                pr_data = item.get("pull_request", {})
                merged_at = pr_data.get("merged_at") if pr_data else None
                state = item.get("state", "")
                if merged_at:
                    state = "merged"

                prs_with_activity.append({
                    "number": pr_number,
                    "title": item.get("title", ""),
                    "state": state,
                    "repository": repo_name,
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "merged_at": merged_at,
                    "closed_at": item.get("closed_at"),
                    "url": item.get("html_url", ""),
                    "has_period_activity": True,
                })

        return prs_with_activity

    def _check_pr_activity_in_period(
        self,
        repo: str,
        pr_number: int,
        start: date,
        end: date
    ) -> bool:  # UC-2.2 | PLAN-3.4
        """
        Check if a PR has any activity (reviews, comments, commits) in the period.

        Args:
            repo: Repository name (owner/repo)
            pr_number: PR number
            start: Start date
            end: End date

        Returns:
            bool: True if PR has activity in the period
        """
        start_str = start.isoformat()
        end_str = end.isoformat()

        # Check reviews
        try:
            reviews = self.gh.api(f"/repos/{repo}/pulls/{pr_number}/reviews")
            if isinstance(reviews, list):
                for review in reviews:
                    review_date = review.get("submitted_at", "")[:10]
                    if start_str <= review_date <= end_str:
                        return True
        except Exception:
            pass

        # Check comments on PR
        try:
            comments = self.gh.api(f"/repos/{repo}/issues/{pr_number}/comments")
            if isinstance(comments, list):
                for comment in comments:
                    comment_date = comment.get("created_at", "")[:10]
                    if start_str <= comment_date <= end_str:
                        return True
        except Exception:
            pass

        # Check commits in date range
        try:
            commits = self.gh.api(f"/repos/{repo}/pulls/{pr_number}/commits")
            if isinstance(commits, list):
                for commit in commits:
                    commit_data = commit.get("commit", {})
                    committer = commit_data.get("committer", {})
                    commit_date = committer.get("date", "")[:10]
                    if start_str <= commit_date <= end_str:
                        return True
        except Exception:
            pass

        return False
