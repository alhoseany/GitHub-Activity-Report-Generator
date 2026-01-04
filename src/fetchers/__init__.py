# =============================================================================
# FILE: src/fetchers/__init__.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
GitHub Data Fetching Package.

This package provides fetchers for different types of GitHub activity data:
- base.py: BaseFetcher with adaptive week/day strategy
- events.py: EventsFetcher for /users/{user}/events API
- commits.py: CommitsFetcher using gh search commits
- pull_requests.py: PullRequestsFetcher using gh search prs
- issues.py: IssuesFetcher using gh search issues
- reviews.py: ReviewsFetcher for PR reviews

Features:
- Adaptive fetching (week -> day granularity for high activity)
- Rate limiting (configurable delay between requests)
- Deduplication of results

Usage:
    from src.fetchers import CommitsFetcher, PullRequestsFetcher
"""
# UC-2.2 | PLAN-3.4

from .base import BaseFetcher
from .events import EventsFetcher
from .commits import CommitsFetcher
from .pull_requests import PullRequestsFetcher
from .issues import IssuesFetcher
from .reviews import ReviewsFetcher

__all__ = [
    "BaseFetcher",
    "EventsFetcher",
    "CommitsFetcher",
    "PullRequestsFetcher",
    "IssuesFetcher",
    "ReviewsFetcher",
]
