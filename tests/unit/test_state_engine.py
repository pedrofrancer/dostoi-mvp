import unittest

from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.state.engine import derive_state
from visual_harness.state.models import AgentState


def ev(event_type, **payload):
    return Event(session_id="sess_1", source="claude-code", type=event_type, payload=payload)


class TestDeriveState(unittest.TestCase):
    """Os seis casos oficiais do TechSpecs Seção 54."""

    def test_1_task_started_is_understanding(self):
        self.assertEqual(derive_state([ev(EventType.TASK_STARTED)]), AgentState.UNDERSTANDING)

    def test_2_file_read_is_reading(self):
        events = [ev(EventType.FILE_READ, path="src/main.py")]
        self.assertEqual(derive_state(events), AgentState.READING)

    def test_3_test_failed_alone_is_error(self):
        events = [ev(EventType.TEST_FAILED, test="login")]
        self.assertEqual(derive_state(events), AgentState.ERROR)

    def test_4_test_failed_then_approach_changed_is_reconsidering(self):
        events = [
            ev(EventType.TEST_FAILED, test="login"),
            ev(EventType.APPROACH_CHANGED),
        ]
        self.assertEqual(derive_state(events), AgentState.RECONSIDERING)

    def test_5_agent_waiting_is_waiting(self):
        self.assertEqual(derive_state([ev(EventType.AGENT_WAITING)]), AgentState.WAITING)

    def test_6_tests_passed_and_completed_is_success(self):
        events = [ev(EventType.TEST_PASSED), ev(EventType.AGENT_COMPLETED)]
        self.assertEqual(derive_state(events), AgentState.SUCCESS)

    # Casos extras: a distinção que o Seção 23 só menciona em prosa.

    def test_no_events_is_unknown(self):
        self.assertEqual(derive_state([]), AgentState.UNKNOWN)

    def test_test_failed_followed_by_investigating_read_is_investigating(self):
        events = [
            ev(EventType.TEST_FAILED, test="login"),
            ev(EventType.FILE_READ, path="src/auth.py"),
        ]
        self.assertEqual(derive_state(events), AgentState.INVESTIGATING)

    def test_file_read_before_test_failed_does_not_count_as_investigating(self):
        events = [
            ev(EventType.FILE_READ, path="src/auth.py"),
            ev(EventType.TEST_FAILED, test="login"),
        ]
        self.assertEqual(derive_state(events), AgentState.ERROR)

    def test_test_suite_completed_with_zero_failures_counts_as_passed(self):
        events = [
            ev(EventType.TEST_SUITE_COMPLETED, passed=33, failed=0),
            ev(EventType.AGENT_COMPLETED),
        ]
        self.assertEqual(derive_state(events), AgentState.SUCCESS)


if __name__ == "__main__":
    unittest.main()
