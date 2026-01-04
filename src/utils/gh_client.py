# =============================================================================
# FILE: src/utils/gh_client.py
# TASKS: UC-2.2, UC-8.1
# PLAN: Section 3.4, 3.5
# =============================================================================
"""
GitHub CLI Client Wrapper.

This module provides a wrapper for gh CLI commands:
- api(): Call GitHub API endpoints
- search(): Execute gh search commands

GitHubClient methods:
- api(endpoint, paginate=False, jq=None): Call API endpoint
- search(search_type, query, limit=100): Execute search

Rate limiting:
- Configurable delay between requests (default: 1 second)
- Respects GitHub rate limits

Caching (UC-8.1 | PLAN-3.5):
- Optionally accepts a ResponseCache instance
- Caches API responses for configured TTL
- Cache is bypassed when --no-cache flag is used
"""
from __future__ import annotations

import json
import subprocess
import time
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .cache import ResponseCache


class GitHubClientError(Exception):  # UC-2.2 | PLAN-3.4
    """Exception raised for GitHub CLI errors."""
    pass


class GitHubClient:  # UC-2.2, UC-8.1 | PLAN-3.4, 3.5
    """
    Wrapper for gh CLI commands.

    Supports optional caching of API responses (UC-8.1).
    """

    def __init__(
        self,
        request_delay: float = 1.0,
        timeout: int = 30,
        cache: ResponseCache | None = None  # UC-8.1 | PLAN-3.5
    ):
        """
        Initialize GitHub client.

        Args:
            request_delay: Seconds to wait between requests (default: 1.0)
            timeout: Timeout for subprocess calls in seconds (default: 30)
            cache: Optional ResponseCache instance for caching API responses
        """
        self.request_delay = request_delay
        self.timeout = timeout
        self.cache = cache  # UC-8.1 | PLAN-3.5
        self._last_request_time: float = 0

    def _rate_limit_pause(self) -> None:  # UC-2.2 | PLAN-3.4
        """Pause between requests to respect rate limits."""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.request_delay:
                time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()

    def _get_cache_key(self, endpoint: str, **kwargs) -> str:  # UC-8.1 | PLAN-3.5
        """Generate a cache key for an API call."""
        parts = [endpoint]
        if kwargs.get("paginate"):
            parts.append("paginate")
        if kwargs.get("jq"):
            parts.append(f"jq={kwargs['jq']}")
        if kwargs.get("method") and kwargs["method"] != "GET":
            parts.append(f"method={kwargs['method']}")
        return "|".join(parts)

    def api(
        self,
        endpoint: str,
        paginate: bool = False,
        jq: str | None = None,
        method: str = "GET"
    ) -> dict[str, Any] | list[dict[str, Any]]:  # UC-2.2, UC-8.1 | PLAN-3.4
        """
        Call GitHub API via gh CLI.

        Checks cache before making API call if cache is enabled (UC-8.1).

        Args:
            endpoint: API endpoint path (e.g., "/users/{user}/events")
            paginate: Enable pagination for large results
            jq: JQ filter expression
            method: HTTP method (default: GET)

        Returns:
            dict | list: API response parsed as JSON

        Raises:
            GitHubClientError: If API call fails
        """
        # UC-8.1 | PLAN-3.5 - Check cache first for GET requests
        cache_key = None
        if self.cache and method == "GET":
            cache_key = self._get_cache_key(endpoint, paginate=paginate, jq=jq, method=method)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        self._rate_limit_pause()

        cmd = ["gh", "api", endpoint]

        if method != "GET":
            cmd.extend(["-X", method])

        if paginate:
            cmd.append("--paginate")

        if jq:
            cmd.extend(["--jq", jq])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown error"
                raise GitHubClientError(f"GitHub API error: {error_msg}")

            output = result.stdout.strip()
            if not output:
                return []

            # Handle paginated results (multiple JSON objects)
            if paginate and "\n" in output and not output.startswith("["):
                # Each line is a separate JSON array, merge them
                items: list[dict[str, Any]] = []
                for line in output.split("\n"):
                    line = line.strip()
                    if line:
                        try:
                            parsed = json.loads(line)
                            if isinstance(parsed, list):
                                items.extend(parsed)
                            else:
                                items.append(parsed)
                        except json.JSONDecodeError:
                            continue
                data = items
            else:
                data = json.loads(output)

            # UC-8.1 | PLAN-3.5 - Store in cache
            if cache_key and self.cache:
                self.cache.set(cache_key, data)

            return data

        except subprocess.TimeoutExpired:
            raise GitHubClientError(f"API request timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise GitHubClientError(f"Failed to parse API response: {e}")

    def search(
        self,
        search_type: str,
        query: str,
        limit: int = 100,
        json_fields: list[str] | None = None
    ) -> list[dict[str, Any]]:  # UC-2.2, UC-8.1 | PLAN-3.4.2
        """
        Execute gh search command.

        Checks cache before making search call if cache is enabled (UC-8.1).

        Args:
            search_type: Type of search ("commits", "prs", "issues")
            query: Search query string
            limit: Maximum results (default: 100)
            json_fields: Fields to include in JSON output

        Returns:
            list[dict]: Search results

        Raises:
            GitHubClientError: If search fails
        """
        # UC-8.1 | PLAN-3.5 - Check cache first
        cache_key = None
        if self.cache:
            cache_key = f"search|{search_type}|{query}|{limit}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        self._rate_limit_pause()

        cmd = ["gh", "search", search_type, query]
        cmd.extend(["--limit", str(limit)])

        # Default JSON fields based on search type
        # Note: Available fields vary by search type
        if json_fields is None:
            if search_type == "commits":
                json_fields = ["sha", "commit", "repository", "url"]
            elif search_type == "prs":
                # Available: assignees, author, authorAssociation, body, closedAt,
                # commentsCount, createdAt, id, isDraft, isLocked, isPullRequest,
                # labels, number, repository, state, title, updatedAt, url
                json_fields = [
                    "number", "title", "state", "url", "repository",
                    "createdAt", "closedAt"
                ]
            elif search_type == "issues":
                json_fields = [
                    "number", "title", "state", "url", "repository",
                    "createdAt", "closedAt", "labels"
                ]
            else:
                json_fields = ["url", "title", "state", "createdAt"]

        cmd.extend(["--json", ",".join(json_fields)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown error"
                # Some search errors are not fatal (e.g., no results)
                if "no results" in error_msg.lower():
                    return []
                raise GitHubClientError(f"GitHub search error: {error_msg}")

            output = result.stdout.strip()
            if not output:
                return []

            data = json.loads(output)

            # UC-8.1 | PLAN-3.5 - Store in cache
            if cache_key and self.cache:
                self.cache.set(cache_key, data)

            return data

        except subprocess.TimeoutExpired:
            raise GitHubClientError(f"Search request timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise GitHubClientError(f"Failed to parse search response: {e}")

    def get_logged_in_user(self) -> str:  # UC-2.1 | PLAN-3.1
        """
        Get currently logged-in GitHub user from gh CLI.

        Returns:
            str: GitHub username

        Raises:
            GitHubClientError: If unable to get user
        """
        try:
            result = subprocess.run(
                ["gh", "api", "/user", "--jq", ".login"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise GitHubClientError(
                    "Failed to get GitHub user. Is gh CLI authenticated?"
                )

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise GitHubClientError("Request timed out getting user info")

    def check_auth(self) -> bool:  # UC-2.1 | PLAN-3.1
        """
        Check if gh CLI is authenticated.

        Returns:
            bool: True if authenticated
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_rate_limit(self) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Get current rate limit status.

        Returns:
            dict: Rate limit information
        """
        try:
            return self.api("/rate_limit")
        except GitHubClientError:
            return {"resources": {"core": {"remaining": -1, "limit": -1}}}
