# =============================================================================
# FILE: src/fetchers/releases.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Releases Fetcher.

This module fetches release data using a tiered approach:
- Tier 1: GitHub Releases API (/repos/{owner}/{repo}/releases)
- Tier 2: Tags API fallback (/repos/{owner}/{repo}/tags)

For each release, it calculates user contribution by analyzing:
- Commits between consecutive tags via the compare API
- PR reviews on merge commits found in the diff

Additional detection:
- Monorepo-scoped tags (e.g., packages/foo/v2.1)
- Anomalies: huge releases, empty releases, rapid releases
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, TYPE_CHECKING

from .base import BaseFetcher

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class ReleasesFetcher(BaseFetcher):  # UC-2.2 | PLAN-3.4
    """Fetch releases and compute user contribution metrics."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        username: str,
        logger: Any = None
    ):
        """
        Initialize releases fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration with fetching settings
            username: GitHub username to measure contribution for
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
        Fetch releases for a date range.

        Note: Releases are not date-searchable via GitHub Search API.
        This method returns an empty list; use fetch_for_repos instead.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Empty list (use fetch_for_repos)
        """
        return []

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """Get unique identifier for a release."""
        repo = event.get("repository", "")
        tag = event.get("tag_name", "")
        if repo and tag:
            return f"{repo}:{tag}"
        return None

    def fetch_for_repos(
        self,
        repos: list[str],
        start_date: date,
        end_date: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch releases across multiple repositories.

        Main entry point. Iterates repos and collects release contributions.

        Args:
            repos: List of repository names (owner/repo)
            start_date: Start of period
            end_date: End of period

        Returns:
            list[dict]: Combined list of enriched release dicts
        """
        all_releases: list[dict[str, Any]] = []

        for repo in repos:
            if self.logger:
                self.logger.info(f"Fetching releases for {repo}")

            repo_releases = self._fetch_repo_releases(repo, start_date, end_date)
            all_releases.extend(repo_releases)

        if self.logger:
            self.logger.info(f"Found {len(all_releases)} total releases across {len(repos)} repos")

        return all_releases

    def _fetch_repo_releases(
        self,
        repo: str,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch releases for a single repository using tiered approach.

        Tier 1: GitHub Releases API
        Tier 2: Tags API fallback (if no releases or API error)

        Args:
            repo: Repository name (owner/repo)
            start: Start date
            end: End date

        Returns:
            list[dict]: Enriched release dicts for the period
        """
        # Tier 1: Try GitHub Releases API
        releases_result = self._fetch_github_releases(repo, start, end)

        if releases_result is not None:
            filtered = releases_result["filtered"]
            all_releases = releases_result["all"]
            detection_method = "github_releases"
        else:
            # Tier 2: Fallback to tags
            if self.logger:
                self.logger.debug(f"Falling back to tags for {repo}")
            tags_result = self._fetch_from_tags(repo, start, end)
            filtered = tags_result["filtered"]
            all_releases = tags_result["all"]
            detection_method = "tags"

        if not filtered:
            if self.logger:
                self.logger.debug(f"No releases found for {repo} in period")
            return []

        if self.logger:
            self.logger.info(f"Found {len(filtered)} releases for {repo} ({detection_method})")

        enriched = self._enrich_releases(repo, filtered, all_releases, detection_method)
        return enriched

    def _fetch_github_releases(
        self,
        repo: str,
        start: date,
        end: date
    ) -> dict[str, Any] | None:  # UC-2.2 | PLAN-3.4
        """
        Fetch releases via GitHub Releases API.

        Args:
            repo: Repository name (owner/repo)
            start: Start date
            end: End date

        Returns:
            dict with 'filtered' and 'all' release lists, or None on error
        """
        try:
            raw_releases = self.gh.api(
                f"/repos/{repo}/releases",
                paginate=True
            )
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to fetch releases for {repo}: {e}")
            return None

        if not isinstance(raw_releases, list):
            raw_releases = [raw_releases] if raw_releases else []

        # Normalize to standard format and sort by published_at ascending
        all_releases: list[dict[str, Any]] = []
        for r in raw_releases:
            published = r.get("published_at", "") or ""
            all_releases.append({
                "tag_name": r.get("tag_name", ""),
                "name": r.get("name", "") or r.get("tag_name", ""),
                "published_at": published,
                "html_url": r.get("html_url", ""),
            })

        all_releases.sort(key=lambda x: x.get("published_at", ""))

        # Filter to period
        filtered: list[dict[str, Any]] = []
        for release in all_releases:
            pub_date = release.get("published_at", "")[:10]
            if pub_date and start.isoformat() <= pub_date <= end.isoformat():
                filtered.append(release)

        return {"filtered": filtered, "all": all_releases}

    def _fetch_from_tags(
        self,
        repo: str,
        start: date,
        end: date
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Fetch releases by inspecting tags and their commit dates.

        Fallback when GitHub Releases API returns nothing or errors.

        Args:
            repo: Repository name (owner/repo)
            start: Start date
            end: End date

        Returns:
            dict with 'filtered' and 'all' tag-based release lists
        """
        try:
            raw_tags = self.gh.api(
                f"/repos/{repo}/tags",
                paginate=True
            )
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to fetch tags for {repo}: {e}")
            return {"filtered": [], "all": []}

        if not isinstance(raw_tags, list):
            raw_tags = [raw_tags] if raw_tags else []

        # Resolve commit dates for each tag
        all_releases: list[dict[str, Any]] = []
        for tag in raw_tags:
            tag_name = tag.get("name", "")
            commit_sha = tag.get("commit", {}).get("sha", "")
            if not commit_sha:
                continue

            self._rate_limit_pause()

            try:
                commit_data = self.gh.api(f"/repos/{repo}/git/commits/{commit_sha}")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to fetch commit {commit_sha[:8]} for tag {tag_name}: {e}")
                continue

            commit_date = ""
            if isinstance(commit_data, dict):
                commit_date = commit_data.get("committer", {}).get("date", "")

            html_url = f"https://github.com/{repo}/releases/tag/{tag_name}"

            all_releases.append({
                "tag_name": tag_name,
                "name": tag_name,
                "published_at": commit_date,
                "html_url": html_url,
            })

        all_releases.sort(key=lambda x: x.get("published_at", ""))

        # Filter to period
        filtered: list[dict[str, Any]] = []
        for release in all_releases:
            pub_date = release.get("published_at", "")[:10]
            if pub_date and start.isoformat() <= pub_date <= end.isoformat():
                filtered.append(release)

        return {"filtered": filtered, "all": all_releases}

    def _enrich_releases(
        self,
        repo: str,
        releases: list[dict[str, Any]],
        all_releases: list[dict[str, Any]],
        detection_method: str
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Enrich releases with contribution data.

        For each release, finds the previous tag and computes contribution
        metrics via the compare API.

        Args:
            repo: Repository name (owner/repo)
            releases: Filtered releases within the period
            all_releases: Full unfiltered release list (for finding previous tag)
            detection_method: How releases were detected ("github_releases" or "tags")

        Returns:
            list[dict]: Enriched release dicts with contribution data
        """
        enriched: list[dict[str, Any]] = []

        for release in releases:
            tag_name = release.get("tag_name", "")

            # Find previous tag in all_releases
            prev_tag = self._find_previous_tag(tag_name, all_releases)
            if prev_tag is None:
                if self.logger:
                    self.logger.debug(
                        f"Skipping {repo}:{tag_name} - no previous tag found"
                    )
                continue

            contribution = self._get_contribution(repo, release, prev_tag, all_releases)
            contribution["detection_method"] = detection_method
            enriched.append(contribution)

        return enriched

    def _find_previous_tag(
        self,
        tag_name: str,
        all_releases: list[dict[str, Any]]
    ) -> str | None:  # UC-2.2 | PLAN-3.4
        """
        Find the tag immediately before the given tag in the sorted list.

        Args:
            tag_name: Current tag name
            all_releases: All releases sorted by published_at ascending

        Returns:
            str | None: Previous tag name, or None if this is the first release
        """
        prev: str | None = None
        for release in all_releases:
            if release.get("tag_name") == tag_name:
                return prev
            prev = release.get("tag_name")
        return None

    def _get_contribution(
        self,
        repo: str,
        release: dict[str, Any],
        prev_tag: str,
        all_releases: list[dict[str, Any]]
    ) -> dict[str, Any]:  # UC-2.2 | PLAN-3.4
        """
        Calculate user contribution between two tags.

        Uses the compare API to get commits, then checks PR reviews
        for merge commits found in the diff.

        Args:
            repo: Repository name (owner/repo)
            release: Current release dict
            prev_tag: Previous tag name for comparison
            all_releases: Full release list (for anomaly detection)

        Returns:
            dict: Enriched release dict with contribution metrics
        """
        tag_name = release.get("tag_name", "")
        total_commits = 0
        user_commits = 0
        pr_numbers: set[int] = set()

        self._rate_limit_pause()

        try:
            compare_data = self.gh.api(
                f"/repos/{repo}/compare/{prev_tag}...{tag_name}"
            )
        except Exception as e:
            if self.logger:
                self.logger.debug(
                    f"Failed to compare {prev_tag}...{tag_name} in {repo}: {e}"
                )
            compare_data = {}

        if isinstance(compare_data, dict):
            commits_list = compare_data.get("commits", [])
            total_commits = compare_data.get("total_commits", len(commits_list))

            merge_pr_pattern = re.compile(r'Merge pull request #(\d+)')

            for commit in commits_list:
                # Check authorship
                author_login = commit.get("author", {}).get("login", "") if commit.get("author") else ""
                if author_login == self.username:
                    user_commits += 1

                # Extract PR numbers from merge commits
                message = commit.get("commit", {}).get("message", "")
                match = merge_pr_pattern.search(message)
                if match:
                    pr_numbers.add(int(match.group(1)))

        total_prs = len(pr_numbers)

        # Check user's reviews on discovered PRs
        user_reviewed_prs = 0
        review_states = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED"}

        for pr_number in pr_numbers:
            self._rate_limit_pause()

            try:
                reviews = self.gh.api(
                    f"/repos/{repo}/pulls/{pr_number}/reviews",
                    paginate=True
                )
            except Exception as e:
                if self.logger:
                    self.logger.debug(
                        f"Failed to fetch reviews for {repo}#{pr_number}: {e}"
                    )
                continue

            if not isinstance(reviews, list):
                reviews = [reviews] if reviews else []

            for review in reviews:
                reviewer = review.get("user", {}).get("login", "") if review.get("user") else ""
                state = review.get("state", "")
                if reviewer == self.username and state in review_states:
                    user_reviewed_prs += 1
                    break

        # Calculate contribution weight
        commit_share = user_commits / total_commits if total_commits > 0 else 0
        review_share = user_reviewed_prs / total_prs if total_prs > 0 else 0
        contribution_weight = round((commit_share * 0.6 + review_share * 0.4) * 100, 1)

        # Detect monorepo and anomalies
        is_monorepo = self._detect_monorepo_tag(tag_name)
        anomalies = self._detect_anomalies(
            total_commits,
            release.get("published_at", ""),
            all_releases
        )

        return {
            "tag_name": tag_name,
            "name": release.get("name", ""),
            "published_at": release.get("published_at", ""),
            "repository": repo,
            "html_url": release.get("html_url", ""),
            "total_commits": total_commits,
            "user_commits": user_commits,
            "total_prs": total_prs,
            "user_reviewed_prs": user_reviewed_prs,
            "contribution_weight": contribution_weight,
            "is_monorepo_release": is_monorepo,
            "anomalies": anomalies,
            "detection_method": "",  # Set by caller
        }

    def _detect_monorepo_tag(self, tag_name: str) -> bool:  # UC-2.2 | PLAN-3.4
        """
        Detect if a tag is scoped to a monorepo package.

        Monorepo tags contain a '/' where the part after the last '/'
        looks like a version string.

        Args:
            tag_name: Tag name to check

        Returns:
            bool: True if tag appears to be monorepo-scoped
        """
        return bool(re.match(r'^.+/v?\d+\.\d+', tag_name))

    def _detect_anomalies(
        self,
        total_commits: int,
        published_at: str,
        all_releases: list[dict[str, Any]]
    ) -> list[str]:  # UC-2.2 | PLAN-3.4
        """
        Detect anomalies in a release.

        Checks for:
        - huge_release: More than 500 commits
        - empty_release: Zero commits
        - rapid_release: Another release on the same day

        Args:
            total_commits: Number of commits in the release
            published_at: Publication date string
            all_releases: All releases for counting same-day releases

        Returns:
            list[str]: List of anomaly identifiers
        """
        anomalies: list[str] = []

        if total_commits > 500:
            anomalies.append("huge_release")

        if total_commits == 0:
            anomalies.append("empty_release")

        # Check for rapid release (same day)
        pub_date = published_at[:10] if published_at else ""
        if pub_date:
            same_day_count = sum(
                1 for r in all_releases
                if r.get("published_at", "")[:10] == pub_date
            )
            if same_day_count > 1:
                anomalies.append("rapid_release")

        return anomalies
