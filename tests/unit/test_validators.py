"""Tests for Leadership OS input validators."""

import pytest

from leadership_os.utils.validators import (
    ValidationError,
    validate_task_title,
    validate_priority,
    validate_task_status,
    validate_break_type,
    validate_time_format,
    validate_date_format,
    validate_minutes,
    validate_opacity,
)


class TestValidateTaskTitle:
    def test_valid_title(self):
        assert validate_task_title("My Task") == "My Task"

    def test_strips_whitespace(self):
        assert validate_task_title("  My Task  ") == "My Task"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_task_title("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_task_title("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_task_title("x" * 201)

    def test_max_length_ok(self):
        title = validate_task_title("x" * 200)
        assert len(title) == 200


class TestValidatePriority:
    def test_valid_priorities(self):
        assert validate_priority("critical") == "critical"
        assert validate_priority("high") == "high"
        assert validate_priority("medium") == "medium"
        assert validate_priority("low") == "low"

    def test_case_insensitive(self):
        assert validate_priority("HIGH") == "high"
        assert validate_priority("Medium") == "medium"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="Invalid priority"):
            validate_priority("urgent")


class TestValidateTaskStatus:
    def test_valid_statuses(self):
        for status in ["pending", "active", "completed", "paused", "archived", "deleted", "carried_forward"]:
            assert validate_task_status(status) == status

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            validate_task_status("done")


class TestValidateBreakType:
    def test_valid_types(self):
        for bt in ["lunch", "dinner", "tea", "personal", "meeting", "custom"]:
            assert validate_break_type(bt) == bt

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="Invalid break type"):
            validate_break_type("coffee")


class TestValidateTimeFormat:
    def test_valid_times(self):
        assert validate_time_format("09:00") == "09:00"
        assert validate_time_format("14:30") == "14:30"
        assert validate_time_format("0:00") == "00:00"

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid time format"):
            validate_time_format("9am")

    def test_invalid_hour(self):
        with pytest.raises(ValidationError, match="Invalid hour"):
            validate_time_format("25:00")

    def test_invalid_minute(self):
        with pytest.raises(ValidationError, match="Invalid minute"):
            validate_time_format("12:60")


class TestValidateDateFormat:
    def test_valid_date(self):
        assert validate_date_format("2026-07-14") == "2026-07-14"

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date_format("07-14-2026")

    def test_invalid_date(self):
        with pytest.raises(ValidationError, match="Invalid date"):
            validate_date_format("2026-02-30")


class TestValidateMinutes:
    def test_valid_minutes(self):
        assert validate_minutes(30) == 30
        assert validate_minutes("45") == 45

    def test_zero_minutes(self):
        assert validate_minutes(0) == 0

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_minutes(-5)

    def test_too_large_raises(self):
        with pytest.raises(ValidationError, match="cannot exceed 24 hours"):
            validate_minutes(1500)

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError, match="Invalid duration"):
            validate_minutes("abc")


class TestValidateOpacity:
    def test_valid_opacity(self):
        assert validate_opacity(0.5) == 0.5
        assert validate_opacity(0.0) == 0.0
        assert validate_opacity(1.0) == 1.0

    def test_invalid_opacity(self):
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            validate_opacity(2.0)

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="Invalid opacity"):
            validate_opacity("transparent")


class TestValidationError:
    def test_error_attributes(self):
        err = ValidationError("title", "Cannot be empty")
        assert err.field == "title"
        assert err.message == "Cannot be empty"
        assert "title" in str(err)
        assert "Cannot be empty" in str(err)
