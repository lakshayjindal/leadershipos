"""Tests for Leadership OS enums."""

from leadership_os.core.enums import TaskStatus, Priority, AppState, BreakType, DayStatus


class TestTaskStatus:
    def test_valid_transitions_from_pending(self):
        transitions = TaskStatus.valid_transitions()[TaskStatus.PENDING]
        assert TaskStatus.ACTIVE in transitions
        assert TaskStatus.ARCHIVED in transitions
        assert TaskStatus.DELETED in transitions
        assert TaskStatus.COMPLETED not in transitions

    def test_valid_transitions_from_active(self):
        transitions = TaskStatus.valid_transitions()[TaskStatus.ACTIVE]
        assert TaskStatus.PAUSED in transitions
        assert TaskStatus.COMPLETED in transitions
        assert TaskStatus.ARCHIVED in transitions
        assert TaskStatus.DELETED in transitions
        assert TaskStatus.PENDING not in transitions

    def test_valid_transitions_from_paused(self):
        transitions = TaskStatus.valid_transitions()[TaskStatus.PAUSED]
        assert TaskStatus.ACTIVE in transitions
        assert TaskStatus.COMPLETED in transitions
        assert TaskStatus.ARCHIVED in transitions
        assert TaskStatus.PENDING not in transitions

    def test_completed_is_final(self):
        transitions = TaskStatus.valid_transitions()[TaskStatus.COMPLETED]
        assert len(transitions) == 0

    def test_can_transition_to(self):
        assert TaskStatus.PENDING.can_transition_to(TaskStatus.ACTIVE)
        assert not TaskStatus.PENDING.can_transition_to(TaskStatus.COMPLETED)
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.PAUSED)
        assert not TaskStatus.COMPLETED.can_transition_to(TaskStatus.ACTIVE)

    def test_string_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ACTIVE.value == "active"
        assert TaskStatus.COMPLETED.value == "completed"


class TestPriority:
    def test_weight_ordering(self):
        assert Priority.CRITICAL.weight < Priority.HIGH.weight
        assert Priority.HIGH.weight < Priority.MEDIUM.weight
        assert Priority.MEDIUM.weight < Priority.LOW.weight

    def test_comparison_operators(self):
        assert Priority.CRITICAL < Priority.HIGH
        assert Priority.HIGH <= Priority.HIGH
        assert Priority.LOW > Priority.MEDIUM
        assert Priority.MEDIUM >= Priority.MEDIUM

    def test_string_values(self):
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestAppState:
    def test_valid_transitions(self):
        transitions = AppState.valid_transitions()[AppState.STARTUP]
        assert AppState.PLANNING in transitions
        assert AppState.WORKING in transitions

    def test_working_transitions(self):
        transitions = AppState.valid_transitions()[AppState.WORKING]
        assert AppState.BREAK in transitions
        assert AppState.IDLE in transitions
        assert AppState.REVIEW in transitions

    def test_break_returns_to_working(self):
        transitions = AppState.valid_transitions()[AppState.BREAK]
        assert AppState.WORKING in transitions

    def test_review_leads_to_shutdown(self):
        transitions = AppState.valid_transitions()[AppState.REVIEW]
        assert AppState.SHUTDOWN in transitions

    def test_invalid_transition(self):
        assert not AppState.STARTUP.can_transition_to(AppState.BREAK)
        assert not AppState.PLANNING.can_transition_to(AppState.BREAK)


class TestBreakType:
    def test_all_types_exist(self):
        assert BreakType.LUNCH.value == "lunch"
        assert BreakType.DINNER.value == "dinner"
        assert BreakType.TEA.value == "tea"
        assert BreakType.PERSONAL.value == "personal"
        assert BreakType.MEETING.value == "meeting"
        assert BreakType.CUSTOM.value == "custom"


class TestDayStatus:
    def test_values(self):
        assert DayStatus.ACTIVE.value == "active"
        assert DayStatus.COMPLETED.value == "completed"
        assert DayStatus.ARCHIVED.value == "archived"
