# =============================================================================
# FILE: src/utils/date_utils.py
# TASKS: UC-2.1, UC-2.5, UC-3.1
# PLAN: Section 3.1, 3.6
# =============================================================================
"""
Date Handling Utilities.

This module provides date calculation helpers for period selection (UC-3.1):

Functions:
- get_period_range(): Get start and end dates for a period (monthly/quarterly)
- get_week_ranges(): Get list of week ranges within a period
- parse_period(): Parse period string into components
- get_current_quarter(): Get current quarter (1-4)
- get_current_month(): Get current month (1-12)
- get_current_year(): Get current year

Quarter date ranges (UC-3.1 | PLAN-3.1):
- Q1: Jan 1 - Mar 31
- Q2: Apr 1 - Jun 30
- Q3: Jul 1 - Sep 30
- Q4: Oct 1 - Dec 31
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Literal, Iterator


def get_current_quarter() -> int:  # UC-3.1 | PLAN-3.1
    """
    Return current quarter (1-4) based on current month.

    Used for quarterly report default value.
    """
    return (datetime.now().month - 1) // 3 + 1


def get_current_month() -> int:  # UC-3.1 | PLAN-3.1
    """
    Return current month (1-12).

    Used for monthly report default value.
    """
    return datetime.now().month


def get_current_year() -> int:  # UC-3.1 | PLAN-3.1
    """
    Return current year.

    Used for default year when not specified via CLI.
    """
    return datetime.now().year


def get_period_range(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> tuple[date, date]:  # UC-3.1 | PLAN-3.1
    """
    Get start and end dates for a period.

    This is the core function for period selection (UC-3.1).
    Handles both monthly and quarterly periods.

    Args:
        year: Year of the period
        period_type: "monthly" or "quarterly"
        period_value: Month (1-12) or quarter (1-4)

    Returns:
        tuple[date, date]: Start and end dates for the period

    Raises:
        ValueError: If period_value is out of range

    Examples:
        >>> get_period_range(2024, "monthly", 6)
        (date(2024, 6, 1), date(2024, 6, 30))

        >>> get_period_range(2024, "quarterly", 2)
        (date(2024, 4, 1), date(2024, 6, 30))
    """
    if period_type == "monthly":  # UC-3.1 | PLAN-3.1
        if not 1 <= period_value <= 12:
            raise ValueError(f"Month must be 1-12, got {period_value}")
        _, last_day = monthrange(year, period_value)
        return (
            date(year, period_value, 1),
            date(year, period_value, last_day)
        )
    else:  # quarterly  # UC-3.1 | PLAN-3.1
        if not 1 <= period_value <= 4:
            raise ValueError(f"Quarter must be 1-4, got {period_value}")
        quarters = {
            1: (date(year, 1, 1), date(year, 3, 31)),
            2: (date(year, 4, 1), date(year, 6, 30)),
            3: (date(year, 7, 1), date(year, 9, 30)),
            4: (date(year, 10, 1), date(year, 12, 31)),
        }
        return quarters[period_value]


def get_period_dates_str(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> tuple[str, str]:  # UC-3.1 | PLAN-3.6
    """
    Get start and end dates for a period as ISO strings.

    Args:
        year: Year of the period
        period_type: "monthly" or "quarterly"
        period_value: Month (1-12) or quarter (1-4)

    Returns:
        tuple[str, str]: Start and end dates as YYYY-MM-DD strings
    """
    start_date, end_date = get_period_range(year, period_type, period_value)
    return (start_date.isoformat(), end_date.isoformat())


def get_week_ranges(
    start_date: date,
    end_date: date
) -> Iterator[tuple[date, date]]:  # UC-2.2 | PLAN-3.4
    """
    Iterate through weeks within a date range.

    Handles partial weeks at boundaries.

    Args:
        start_date: Start of the period
        end_date: End of the period

    Yields:
        tuple[date, date]: Start and end dates for each week
    """
    current = start_date
    while current <= end_date:
        week_end = min(current + timedelta(days=6), end_date)
        yield (current, week_end)
        current = week_end + timedelta(days=1)


def parse_period(period_str: str) -> tuple[int, str, int]:  # UC-3.1 | PLAN-3.1
    """
    Parse period string into components.

    Args:
        period_str: Period string like "2024-12" (monthly) or "2024-Q4" (quarterly)

    Returns:
        tuple[int, str, int]: (year, period_type, period_value)

    Raises:
        ValueError: If period string is invalid

    Examples:
        >>> parse_period("2024-12")
        (2024, "monthly", 12)

        >>> parse_period("2024-Q4")
        (2024, "quarterly", 4)
    """
    if "-Q" in period_str:
        # Quarterly format: 2024-Q4
        parts = period_str.split("-Q")
        if len(parts) != 2:
            raise ValueError(f"Invalid quarterly period format: {period_str}")
        year = int(parts[0])
        quarter = int(parts[1])
        if not 1 <= quarter <= 4:
            raise ValueError(f"Quarter must be 1-4, got {quarter}")
        return (year, "quarterly", quarter)
    else:
        # Monthly format: 2024-12
        parts = period_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid monthly period format: {period_str}")
        year = int(parts[0])
        month = int(parts[1])
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be 1-12, got {month}")
        return (year, "monthly", month)


def format_period(
    year: int,
    period_type: Literal["monthly", "quarterly"],
    period_value: int
) -> str:  # UC-3.1 | PLAN-3.6
    """
    Format period as string.

    Args:
        year: Year of the period
        period_type: "monthly" or "quarterly"
        period_value: Month (1-12) or quarter (1-4)

    Returns:
        str: Formatted period string (e.g., "2024-12" or "2024-Q4")
    """
    if period_type == "monthly":
        return f"{year}-{period_value:02d}"
    else:
        return f"{year}-Q{period_value}"


def is_within_range(
    check_date: date | str,
    start_date: date,
    end_date: date
) -> bool:  # UC-2.3 | PLAN-4.1
    """
    Check if a date is within a range.

    Args:
        check_date: Date to check (date object or ISO string)
        start_date: Start of range
        end_date: End of range

    Returns:
        bool: True if date is within range (inclusive)
    """
    if isinstance(check_date, str):
        try:
            check_date = date.fromisoformat(check_date[:10])
        except (ValueError, TypeError):
            return False
    return start_date <= check_date <= end_date


def parse_iso_datetime(dt_str: str | None) -> datetime | None:  # UC-2.3 | PLAN-4.1
    """
    Parse ISO datetime string to datetime object.

    Args:
        dt_str: ISO datetime string (e.g., "2024-12-01T12:00:00Z")

    Returns:
        datetime | None: Parsed datetime or None if invalid
    """
    if not dt_str:
        return None
    try:
        # Handle Z suffix
        dt_str = dt_str.rstrip("Z")
        # Handle timezone offset
        if "+" in dt_str:
            dt_str = dt_str.split("+")[0]
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def parse_iso_date(date_str: str | None) -> date | None:  # UC-2.3 | PLAN-4.1
    """
    Parse ISO date string to date object.

    Args:
        date_str: ISO date string (e.g., "2024-12-01" or "2024-12-01T12:00:00Z")

    Returns:
        date | None: Parsed date or None if invalid
    """
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None
