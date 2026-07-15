"""Tests for Leadership OS event bus."""

from leadership_os.core.event_bus import EventBus, TASK_COMPLETED, TIMER_STARTED


class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append((event, data))

        bus.subscribe(TASK_COMPLETED, handler)
        bus.emit(TASK_COMPLETED, {"task_id": "123"})

        assert len(received) == 1
        assert received[0][0] == TASK_COMPLETED
        assert received[0][1] == {"task_id": "123"}

    def test_multiple_subscribers(self):
        bus = EventBus()
        results_a = []
        results_b = []

        def handler_a(event, data):
            results_a.append(data)

        def handler_b(event, data):
            results_b.append(data)

        bus.subscribe(TASK_COMPLETED, handler_a)
        bus.subscribe(TASK_COMPLETED, handler_b)
        bus.emit(TASK_COMPLETED, {"task": "test"})

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append(data)

        bus.subscribe(TIMER_STARTED, handler)
        bus.unsubscribe(TIMER_STARTED, handler)
        bus.emit(TIMER_STARTED, {"timer": "1"})

        assert len(received) == 0

    def test_emit_no_subscribers(self):
        bus = EventBus()
        # Should not raise
        bus.emit("nonexistent_event", {"key": "value"})

    def test_emit_with_no_data(self):
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append(data)

        bus.subscribe(TIMER_STARTED, handler)
        bus.emit(TIMER_STARTED)

        assert len(received) == 1
        assert received[0] == {}

    def test_event_history(self):
        bus = EventBus()
        bus.emit(TASK_COMPLETED, {"task": "1"})
        bus.emit(TIMER_STARTED, {"timer": "2"})
        history = bus.get_history()
        assert len(history) == 2
        assert history[0][0] == TASK_COMPLETED
        assert history[1][0] == TIMER_STARTED

    def test_history_limit(self):
        bus = EventBus()
        for i in range(150):
            bus.emit("event", {"i": i})
        history = bus.get_history(limit=100)
        assert len(history) == 100
        # Should have the last 100 events
        assert history[0][1]["i"] == 50

    def test_clear_subscribers(self):
        bus = EventBus()
        received = []

        def handler(event, data):
            received.append(data)

        bus.subscribe(TASK_COMPLETED, handler)
        bus.clear()
        bus.emit(TASK_COMPLETED, {"task": "test"})

        assert len(received) == 0

    def test_subscriber_count(self):
        bus = EventBus()
        assert bus.subscriber_count(TASK_COMPLETED) == 0

        def handler(event, data):
            pass

        bus.subscribe(TASK_COMPLETED, handler)
        assert bus.subscriber_count(TASK_COMPLETED) == 1

        bus.subscribe(TASK_COMPLETED, handler)
        assert bus.subscriber_count(TASK_COMPLETED) == 2

    def test_handler_exception_does_not_break_others(self):
        bus = EventBus()
        results = []

        def bad_handler(event, data):
            raise ValueError("Intentional error")

        def good_handler(event, data):
            results.append("ok")

        bus.subscribe(TASK_COMPLETED, bad_handler)
        bus.subscribe(TASK_COMPLETED, good_handler)
        bus.emit(TASK_COMPLETED, {"task": "test"})

        assert len(results) == 1
        assert results[0] == "ok"
