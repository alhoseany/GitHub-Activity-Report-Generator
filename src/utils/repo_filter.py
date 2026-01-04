# =============================================================================
# FILE: src/utils/repo_filter.py
# TASKS: UC-5.1
# PLAN: Section 3.3
# =============================================================================
"""
Repository Filtering Utilities.

This module provides functions for filtering repositories based on:
- Whitelist (include list)
- Blacklist (exclude list)
- Private repository flag
- Fork flag

Functions:
- filter_repositories(): Filter a list of repository dictionaries
- filter_items_by_repo(): Filter activity items (commits, PRs, etc.) by repo
- extract_repo_from_url(): Extract owner/repo from a GitHub URL

Usage:
    from src.utils.repo_filter import filter_repositories, filter_items_by_repo
    from src.config.settings import RepositoryConfig

    config = RepositoryConfig(
        include_private=True,
        include_forks=False,
        include=["owner/repo1"],  # whitelist
        exclude=["owner/fork-repo"],  # blacklist
    )

    # Filter repositories
    filtered = filter_repositories(repos, config)

    # Filter activity items by repository
    filtered_commits = filter_items_by_repo(commits, config)
"""
from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.settings import RepositoryConfig


def filter_repositories(
    repositories: list[dict[str, Any]],
    config: RepositoryConfig,
) -> list[dict[str, Any]]:  # UC-5.1 | PLAN-3.3
    """
    Filter a list of repositories based on configuration.

    Args:
        repositories: List of repository dictionaries with keys:
            - full_name: "owner/repo"
            - private: bool (optional)
            - fork: bool (optional)
        config: RepositoryConfig with filtering rules

    Returns:
        list[dict]: Filtered list of repositories

    Example:
        >>> repos = [
        ...     {"full_name": "owner/repo1", "private": False, "fork": False},
        ...     {"full_name": "owner/fork-repo", "private": False, "fork": True},
        ... ]
        >>> config = RepositoryConfig(include_forks=False)
        >>> filtered = filter_repositories(repos, config)
        >>> len(filtered)
        1
    """
    return [repo for repo in repositories if config.should_include(repo)]


def filter_items_by_repo(
    items: list[dict[str, Any]],
    config: RepositoryConfig,
    repo_key: str = "repository",
) -> list[dict[str, Any]]:  # UC-5.1 | PLAN-3.3
    """
    Filter activity items (commits, PRs, issues, etc.) by repository.

    This function extracts the repository information from each item
    and filters based on the repository configuration.

    Args:
        items: List of activity items (commits, PRs, issues, etc.)
        config: RepositoryConfig with filtering rules
        repo_key: Key in the item dict that contains repo info.
            Common values: "repository", "repo", or items may have "url"

    Returns:
        list[dict]: Filtered list of items

    Example:
        >>> items = [
        ...     {"url": "https://github.com/owner/repo1/commit/abc"},
        ...     {"url": "https://github.com/owner/excluded/commit/def"},
        ... ]
        >>> config = RepositoryConfig(exclude=["owner/excluded"])
        >>> filtered = filter_items_by_repo(items, config)
    """
    filtered: list[dict[str, Any]] = []

    for item in items:
        # Try to get repo info from the item
        repo_info = _extract_repo_info(item, repo_key)

        if repo_info is None:
            # If we can't determine the repo, include the item by default
            filtered.append(item)
            continue

        # Check if this repo should be included
        if config.should_include(repo_info):
            filtered.append(item)

    return filtered


def _extract_repo_info(
    item: dict[str, Any],
    repo_key: str = "repository",
) -> dict[str, Any] | None:  # UC-5.1 | PLAN-3.3
    """
    Extract repository information from an activity item.

    Tries multiple strategies:
    1. Direct repo_key access (e.g., item["repository"])
    2. Extract from URL fields (url, html_url, repository_url)
    3. Extract from nested repo field

    Args:
        item: Activity item dictionary
        repo_key: Primary key to check for repo info

    Returns:
        dict | None: Repository info dict with "full_name" key, or None
    """
    # Strategy 1: Direct access via repo_key
    if repo_key in item:
        repo = item[repo_key]
        if isinstance(repo, dict) and "full_name" in repo:
            return repo
        elif isinstance(repo, str):
            # Might be just the full_name string
            return {"full_name": repo}

    # Strategy 2: Extract from URL fields
    for url_key in ["url", "html_url", "repository_url"]:
        if url_key in item and item[url_key]:
            full_name = extract_repo_from_url(item[url_key])
            if full_name:
                return {"full_name": full_name}

    # Strategy 3: Check for nested repo field
    if "repo" in item:
        repo = item["repo"]
        if isinstance(repo, dict) and "name" in repo:
            # GitHub Events API format
            return {"full_name": repo.get("name", "")}

    return None


def extract_repo_from_url(url: str) -> str | None:  # UC-5.1 | PLAN-3.3
    """
    Extract owner/repo from a GitHub URL.

    Handles various GitHub URL formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/pull/123
    - https://github.com/owner/repo/commit/abc123
    - https://api.github.com/repos/owner/repo/...

    Args:
        url: GitHub URL string

    Returns:
        str | None: Repository full name (owner/repo) or None

    Example:
        >>> extract_repo_from_url("https://github.com/octocat/Hello-World/pull/1")
        'octocat/Hello-World'
        >>> extract_repo_from_url("https://api.github.com/repos/owner/repo/commits")
        'owner/repo'
    """
    if not url:
        return None

    # Pattern for github.com URLs
    github_pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)"

    # Pattern for api.github.com URLs
    api_pattern = r"https?://api\.github\.com/repos/([^/]+)/([^/]+)"

    for pattern in [github_pattern, api_pattern]:
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            # Remove any trailing parts (like .git)
            repo = repo.rstrip(".git")
            return f"{owner}/{repo}"

    return None


def parse_repo_list(repos_str: str | None) -> list[str]:  # UC-5.1 | PLAN-3.3
    """
    Parse a comma-separated list of repositories.

    Used for parsing CLI arguments like --include-repos and --exclude-repos.

    Args:
        repos_str: Comma-separated string of repos (e.g., "owner/repo1,owner/repo2")

    Returns:
        list[str]: List of repository names

    Example:
        >>> parse_repo_list("owner/repo1, owner/repo2, owner/repo3")
        ['owner/repo1', 'owner/repo2', 'owner/repo3']
        >>> parse_repo_list(None)
        []
        >>> parse_repo_list("")
        []
    """
    if not repos_str:
        return []

    # Split by comma and strip whitespace
    repos = [r.strip() for r in repos_str.split(",")]

    # Filter out empty strings
    return [r for r in repos if r]
