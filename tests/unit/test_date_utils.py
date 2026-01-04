# =============================================================================
# FILE: tests/unit/test_date_utils.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for date utility functions.  # UC-13.1 | PLAN-4

Tests:
- get_period_range for monthly and quarterly periods
- parse_period for various formats
- Edge cases: end of month, leap years, year boundaries
"""
import pytest
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.date_utils import (
    get_period_range,
    parse_period,
    get_current_quarter,
    get_current_month,
    get_current_year,
    format_period,
    get_period_dates_str,
    is_within_range,
    parse_iso_datetime,
    parse_iso_date,
)


class TestGetPeriodRange:  # UC-13.1 | PLAN-4
    """Tests for get_period_range function."""

    def test_monthly_period_january(self):
        """Test monthly period for January."""
        start, end = get_period_range(2024, "monthly", 1)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_monthly_period_february_leap_year(self):
        """Test February in a leap year."""
        start, end = get_period_range(2024, "monthly", 2)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # 2024 is a leap year

    def test_monthly_period_february_non_leap_year(self):
        """Test February in a non-leap year."""
        start, end = get_period_range(2023, "monthly", 2)
        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)

    def test_monthly_period_december(self):
        """Test monthly period for December."""
        start, end = get_period_range(2024, "monthly", 12)
        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_quarterly_period_q1(self):
        """Test Q1 period (Jan-Mar)."""
        start, end = get_period_range(2024, "quarterly", 1)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_quarterly_period_q2(self):
        """Test Q2 period (Apr-Jun)."""
        start, end = get_period_range(2024, "quarterly", 2)
        assert start == date(2024, 4, 1)
        assert end == date(2024, 6, 30)

    def test_quarterly_period_q3(self):
        """Test Q3 period (Jul-Sep)."""
        start, end = get_period_range(2024, "quarterly", 3)
        assert start == date(2024, 7, 1)
        assert end == date(2024, 9, 30)

    def test_quarterly_period_q4(self):
        """Test Q4 period (Oct-Dec)."""
        start, end = get_period_range(2024, "quarterly", 4)
        assert start == date(2024, 10, 1)
        assert end == date(2024, 12, 31)

    def test_invalid_month_raises_error(self):
        """Test that invalid month raises ValueError."""
        with pytest.raises(ValueError):
            get_period_range(2024, "monthly", 13)

    def test_invalid_quarter_raises_error(self):
        """Test that invalid quarter raises ValueError."""
        with pytest.raises(ValueError):
            get_period_range(2024, "quarterly", 5)

    def test_zero_month_raises_error(self):
        """Test that zero month raises ValueError."""
        with pytest.raises(ValueError):
            get_period_range(2024, "monthly", 0)


class TestParsePeriod:  # UC-13.1 | PLAN-4
    """Tests for parse_period function."""

    def test_parse_monthly_format(self):
        """Test parsing monthly format YYYY-MM."""
        year, period_type, period = parse_period("2024-12")
        assert year == 2024
        assert period == 12
        assert period_type == "monthly"

    def test_parse_quarterly_format(self):
        """Test parsing quarterly format YYYY-QN."""
        year, period_type, period = parse_period("2024-Q4")
        assert year == 2024
        assert period == 4
        assert period_type == "quarterly"

    def test_parse_monthly_single_digit(self):
        """Test parsing monthly format with single digit."""
        year, period_type, period = parse_period("2024-01")
        assert year == 2024
        assert period == 1
        assert period_type == "monthly"

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_period("invalid")

    def test_parse_invalid_month_raises_error(self):
        """Test that invalid month raises ValueError."""
        with pytest.raises(ValueError):
            parse_period("2024-13")

    def test_parse_invalid_quarter_raises_error(self):
        """Test that invalid quarter raises ValueError."""
        with pytest.raises(ValueError):
            parse_period("2024-Q5")


class TestGetCurrentPeriod:  # UC-13.1 | PLAN-4
    """Tests for get_current_* functions."""

    def test_get_current_quarter_returns_int(self):
        """Test that get_current_quarter returns an integer."""
        result = get_current_quarter()
        assert isinstance(result, int)
        assert 1 <= result <= 4

    def test_get_current_month_returns_int(self):
        """Test that get_current_month returns an integer."""
        result = get_current_month()
        assert isinstance(result, int)
        assert 1 <= result <= 12

    def test_get_current_year_returns_int(self):
        """Test that get_current_year returns an integer."""
        result = get_current_year()
        assert isinstance(result, int)
        assert 2020 <= result <= 2100


class TestFormatPeriod:  # UC-13.1 | PLAN-4
    """Tests for format_period function."""

    def test_format_monthly(self):
        """Test formatting monthly period."""
        result = format_period(2024, "monthly", 12)
        assert result == "2024-12"

    def test_format_monthly_with_leading_zero(self):
        """Test formatting month with leading zero."""
        result = format_period(2024, "monthly", 1)
        assert result == "2024-01"

    def test_format_quarterly(self):
        """Test formatting quarterly period."""
        result = format_period(2024, "quarterly", 4)
        assert result == "2024-Q4"


class TestGetPeriodDatesStr:  # UC-13.1 | PLAN-4
    """Tests for get_period_dates_str function."""

    def test_returns_string_tuple(self):
        """Test that function returns tuple of strings."""
        start, end = get_period_dates_str(2024, "monthly", 12)
        assert isinstance(start, str)
        assert isinstance(end, str)

    def test_monthly_date_format(self):
        """Test monthly date string format."""
        start, end = get_period_dates_str(2024, "monthly", 12)
        assert start == "2024-12-01"
        assert end == "2024-12-31"

    def test_quarterly_date_format(self):
        """Test quarterly date string format."""
        start, end = get_period_dates_str(2024, "quarterly", 4)
        assert start == "2024-10-01"
        assert end == "2024-12-31"


class TestIsWithinRange:  # UC-13.1 | PLAN-4
    """Tests for is_within_range function."""

    def test_date_within_range(self):
        """Test date within range returns True."""
        assert is_within_range(
            date(2024, 12, 15),
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is True

    def test_date_before_range(self):
        """Test date before range returns False."""
        assert is_within_range(
            date(2024, 11, 30),
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is False

    def test_date_after_range(self):
        """Test date after range returns False."""
        assert is_within_range(
            date(2025, 1, 1),
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is False

    def test_date_on_start_boundary(self):
        """Test date on start boundary returns True."""
        assert is_within_range(
            date(2024, 12, 1),
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is True

    def test_date_on_end_boundary(self):
        """Test date on end boundary returns True."""
        assert is_within_range(
            date(2024, 12, 31),
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is True

    def test_string_date_within_range(self):
        """Test string date within range."""
        assert is_within_range(
            "2024-12-15",
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is True

    def test_invalid_string_returns_false(self):
        """Test invalid string returns False."""
        assert is_within_range(
            "invalid",
            date(2024, 12, 1),
            date(2024, 12, 31)
        ) is False


class TestParseIsoDatetime:  # UC-13.1 | PLAN-4
    """Tests for parse_iso_datetime function."""

    def test_parse_valid_datetime(self):
        """Test parsing valid datetime string."""
        result = parse_iso_datetime("2024-12-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 15

    def test_parse_without_z(self):
        """Test parsing datetime without Z suffix."""
        result = parse_iso_datetime("2024-12-15T10:30:00")
        assert result is not None

    def test_parse_none_returns_none(self):
        """Test parsing None returns None."""
        assert parse_iso_datetime(None) is None

    def test_parse_invalid_returns_none(self):
        """Test parsing invalid string returns None."""
        assert parse_iso_datetime("invalid") is None


class TestParseIsoDate:  # UC-13.1 | PLAN-4
    """Tests for parse_iso_date function."""

    def test_parse_valid_date(self):
        """Test parsing valid date string."""
        result = parse_iso_date("2024-12-15")
        assert result is not None
        assert result == date(2024, 12, 15)

    def test_parse_datetime_extracts_date(self):
        """Test parsing datetime string extracts date."""
        result = parse_iso_date("2024-12-15T10:30:00Z")
        assert result is not None
        assert result == date(2024, 12, 15)

    def test_parse_none_returns_none(self):
        """Test parsing None returns None."""
        assert parse_iso_date(None) is None

    def test_parse_invalid_returns_none(self):
        """Test parsing invalid string returns None."""
        assert parse_iso_date("invalid") is None
