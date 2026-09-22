import unittest

from visual_harness.context.engine import compute_context
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.state.models import AgentState


def ev(event_type, **payload):
    return Event(session_id="sess_1", source="claude-code", type=event_type, payload=payload)


class TestComputeContext(unittest.TestCase):
    def test_empty_events_has_no_task_and_unknown_state(self):
        context = compute_context([], agent="claude-code")
        self.assertIsNone(context.task)
        self.assertEqual(context.current_state, AgentState.UNKNOWN)
        self.assertEqual(context.modified_files, [])
        self.assertEqual(context.tests_passed, 0)
        self.assertEqual(context.tests_failed, 0)

    def test_task_started_sets_task(self):
        context = compute_context(
            [ev(EventType.TASK_STARTED, description="Implementar login")],
            agent="claude-code",
        )
        self.assertEqual(context.task, "Implementar login")

    def test_task_changed_overrides_task_started(self):
        events = [
            ev(EventType.TASK_STARTED, description="Primeira tarefa"),
            ev(EventType.TASK_CHANGED, description="Tarefa nova"),
        ]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.task, "Tarefa nova")

    def test_modified_files_deduplicated_and_ordered(self):
        events = [
            ev(EventType.FILE_MODIFIED, path="a.py"),
            ev(EventType.FILE_CREATED, path="b.py"),
            ev(EventType.FILE_MODIFIED, path="a.py"),
        ]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.modified_files, ["a.py", "b.py"])

    def test_file_read_does_not_count_as_modified(self):
        context = compute_context(
            [ev(EventType.FILE_READ, path="a.py")], agent="claude-code"
        )
        self.assertEqual(context.modified_files, [])

    def test_tests_passed_and_failed_counts(self):
        events = [
            ev(EventType.TEST_PASSED),
            ev(EventType.TEST_PASSED),
            ev(EventType.TEST_FAILED, test="login"),
        ]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.tests_passed, 2)
        self.assertEqual(context.tests_failed, 1)

    def test_test_suite_completed_adds_to_counts(self):
        events = [ev(EventType.TEST_SUITE_COMPLETED, passed=33, failed=2)]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.tests_passed, 33)
        self.assertEqual(context.tests_failed, 2)

    def test_test_failed_and_agent_error_populate_recent_errors(self):
        events = [
            ev(EventType.TEST_FAILED, test="login"),
            ev(EventType.AGENT_ERROR, message="import quebrado"),
        ]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.recent_errors, ["falha: login", "import quebrado"])

    def test_recent_errors_bounded(self):
        events = [ev(EventType.AGENT_ERROR, message=f"erro {i}") for i in range(15)]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(len(context.recent_errors), 10)
        self.assertEqual(context.recent_errors[-1], "erro 14")

    def test_current_state_reflects_derive_state(self):
        events = [ev(EventType.AGENT_WAITING)]
        context = compute_context(events, agent="claude-code")
        self.assertEqual(context.current_state, AgentState.WAITING)

    def test_agent_field_is_passed_through(self):
        context = compute_context([], agent="claude-code")
        self.assertEqual(context.agent, "claude-code")


if __name__ == "__main__":
    unittest.main()
