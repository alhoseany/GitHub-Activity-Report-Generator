# =============================================================================
# FILE: src/fetchers/base.py
# TASKS: UC-2.2
# PLAN: Section 3.4
# =============================================================================
"""
Base Fetcher Class.

This module provides the BaseFetcher class that implements:
- Adaptive fetching strategy (week -> day granularity)
- Rate limiting between requests
- Deduplication of results
- Logging integration

Methods:
- fetch_period(): Fetch data for a date range with adaptive strategy
- _iter_weeks(): Iterate through weeks in a date range
- _fetch_week_by_days(): Fetch high-activity week day by day
- _fetch_range(): Abstract method to fetch data (override in subclasses)
- _deduplicate(): Remove duplicate records
- _get_event_id(): Get unique identifier for an event
"""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.gh_client import GitHubClient


class BaseFetcher:  # UC-2.2 | PLAN-3.4
    """Base class for all data fetchers with adaptive strategy."""

    def __init__(
        self,
        gh_client: GitHubClient,
        config: Any,
        logger: Any = None
    ):
        """
        Initialize fetcher.

        Args:
            gh_client: GitHub client instance
            config: Configuration object or dict with fetching settings
            logger: Optional logger instance
        """
        self.gh = gh_client
        self.config = config
        self.logger = logger

        # Get config values with defaults
        if hasattr(config, 'high_activity_threshold'):
            self.high_activity_threshold = config.high_activity_threshold
        elif isinstance(config, dict):
            self.high_activity_threshold = config.get('high_activity_threshold', 100)
        else:
            self.high_activity_threshold = 100

        if hasattr(config, 'request_delay'):
            self.request_delay = config.request_delay
        elif isinstance(config, dict):
            self.request_delay = config.get('request_delay', 1.0)
        else:
            self.request_delay = 1.0

    def fetch_period(
        self,
        start_date: date,
        end_date: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch data for a period using adaptive week/day granularity.

        Algorithm:
        1. Split period into weeks (7-day chunks)
        2. Fetch each week's data
        3. If week has >= high_activity_threshold events, re-fetch day-by-day
        4. Merge and deduplicate results

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            list[dict]: Deduplicated events for the period
        """
        all_events: list[dict[str, Any]] = []

        for week_start, week_end in self._iter_weeks(start_date, end_date):
            # First attempt: fetch entire week
            week_events = self._fetch_range(week_start, week_end)

            # Check if high activity
            if len(week_events) >= self.high_activity_threshold:
                if self.logger:
                    self.logger.info(
                        f"High activity week ({len(week_events)} events), "
                        f"switching to daily fetching"
                    )
                # Re-fetch day by day
                week_events = self._fetch_week_by_days(week_start, week_end)

            all_events.extend(week_events)

        return self._deduplicate(all_events)

    def _iter_weeks(
        self,
        start: date,
        end: date
    ) -> Iterator[tuple[date, date]]:  # UC-2.2 | PLAN-3.4
        """
        Iterate through weeks, handling partial weeks at boundaries.

        Args:
            start: Start date
            end: End date

        Yields:
            tuple[date, date]: Start and end dates for each week
        """
        current = start
        while current <= end:
            week_end = min(current + timedelta(days=6), end)
            yield (current, week_end)
            current = week_end + timedelta(days=1)

    def _fetch_week_by_days(
        self,
        week_start: date,
        week_end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch a high-activity week day by day.

        Args:
            week_start: Start of week
            week_end: End of week

        Returns:
            list[dict]: All events for the week
        """
        daily_events: list[dict[str, Any]] = []
        current = week_start

        while current <= week_end:
            day_events = self._fetch_range(current, current)
            daily_events.extend(day_events)
            current += timedelta(days=1)

        return daily_events

    def _fetch_range(
        self,
        start: date,
        end: date
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Fetch data for a date range.

        Override in subclasses to implement specific API calls.

        Args:
            start: Start date
            end: End date

        Returns:
            list[dict]: Events for the date range
        """
        raise NotImplementedError("Subclasses must implement _fetch_range")

    def _deduplicate(
        self,
        events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # UC-2.2 | PLAN-3.4
        """
        Remove duplicate events based on unique identifier.

        Args:
            events: List of events

        Returns:
            list[dict]: Deduplicated events
        """
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []

        for event in events:
            event_id = self._get_event_id(event)
            if event_id and event_id not in seen:
                seen.add(event_id)
                unique.append(event)
            elif not event_id:
                # Include events without ID (can't deduplicate)
                unique.append(event)

        return unique

    def _get_event_id(self, event: dict[str, Any]) -> str | None:  # UC-2.2 | PLAN-3.4
        """
        Get unique identifier for an event.

        Override in subclasses for specific ID fields.

        Args:
            event: Event dictionary

        Returns:
            str | None: Unique identifier or None
        """
        return event.get("id") or event.get("sha") or event.get("url")

    def _rate_limit_pause(self) -> None:  # UC-2.2 | PLAN-3.4
        """Pause between requests to respect rate limits."""
        time.sleep(self.request_delay)
