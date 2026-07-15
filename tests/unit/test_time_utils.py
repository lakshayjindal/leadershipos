"""Tests for Leadership OS time utilities."""

from datetime import datetime, timedelta
from unittest.mock import patch

from leadership_os.utils.time_utils import (
    format_duration,
    format_duration_compact,
    format_duration_short,
    parse_time_string,
    calculate_elapsed,
    format_time_display,
    get_time_of_day,
)


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "00:00:00"

    def test_seconds_only(self):
        assert format_duration(45) == "00:00:45"

    def test_minutes_and_seconds(self):
        assert format_duration(125) == "00:02:05"

    def test_hours_minutes_seconds(self):
        assert format_duration(3661) == "01:01:01"

    def test_large_duration(self):
        assert format_duration(36000) == "10:00:00"

    def test_negative_returns_zero(self):
        assert format_duration(-10) == "00:00:00"


class TestFormatDurationCompact:
    def test_zero(self):
        assert format_duration_compact(0) == "0s"

    def test_seconds(self):
        assert format_duration_compact(45) == "45s"

    def test_minutes(self):
        assert format_duration_compact(300) == "5m"

    def test_hours_and_minutes(self):
        assert format_duration_compact(3661) == "1h 1m"

    def test_hours_only(self):
        assert format_duration_compact(7200) == "2h 0m"

    def test_negative_returns_zero(self):
        assert format_duration_compact(-5) == "0s"


class TestFormatDurationShort:
    def test_zero(self):
        assert format_duration_short(0) == "0m"

    def test_minutes(self):
        assert format_duration_short(65) == "1m"

    def test_hours(self):
        assert format_duration_short(3600) == "1h"

    def test_hours_and_minutes(self):
        assert format_duration_short(5400) == "1h 30m"

    def test_minimum_one_minute(self):
        assert format_duration_short(30) == "1m"


class TestParseTimeString:
    def test_valid_time(self):
        assert parse_time_string("09:00") == (9, 0)

    def test_valid_afternoon(self):
        assert parse_time_string("14:30") == (14, 30)

    def test_midnight(self):
        assert parse_time_string("00:00") == (0, 0)

    def test_end_of_day(self):
        assert parse_time_string("23:59") == (23, 59)

    def test_invalid_format(self):
        import pytest
        with pytest.raises(ValueError):
            parse_time_string("invalid")

    def test_invalid_hour(self):
        import pytest
        with pytest.raises(ValueError):
            parse_time_string("25:00")

    def test_invalid_minute(self):
        import pytest
        with pytest.raises(ValueError):
            parse_time_string("12:60")


class TestCalculateElapsed:
    def test_recent_timestamp(self):
        now = datetime.now()
        timestamp = now.isoformat()
        elapsed = calculate_elapsed(timestamp)
        assert 0 <= elapsed <= 2  # Allow small timing difference

    def test_past_timestamp(self):
        past = datetime.now() - timedelta(hours=2)
        elapsed = calculate_elapsed(past.isoformat())
        assert elapsed == 7200

    def test_invalid_timestamp(self):
        assert calculate_elapsed("not-a-timestamp") == 0


class TestFormatTimeDisplay:
    def test_none_returns_default(self):
        assert format_time_display(None) == "--:--"

    def test_valid_time(self):
        # ISO timestamp
        ts = "2026-07-14T09:30:00"
        assert format_time_display(ts) == "09:30"

    def test_plain_time(self):
        assert format_time_display("14:00") == "14:00"


class TestGetTimeOfDay:
    def test_returns_hh_mm(self):
        result = get_time_of_day()
        assert len(result) == 5
        assert result[2] == ":"
        hour, minute = result.split(":")
        assert 0 <= int(hour) <= 23
        assert 0 <= int(minute) <= 59
