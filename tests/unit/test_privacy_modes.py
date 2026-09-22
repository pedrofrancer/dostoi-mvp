import unittest

from visual_harness.context.models import SessionContext
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.privacy.modes import (
    PrivacyMode,
    prepare_context_for_persistence,
    prepare_event_for_persistence,
)
from visual_harness.state.models import AgentState


def make_event(**payload):
    return Event(session_id="s1", source="claude-code", type=EventType.COMMAND_STARTED, payload=payload)


class TestPrepareEventForPersistence(unittest.TestCase):
    def test_strict_strips_payload_entirely(self):
        event = make_event(command="API_KEY=abc123 npm start")
        result = prepare_event_for_persistence(event, PrivacyMode.STRICT)
        self.assertEqual(result.payload, {})

    def test_standard_redacts_payload(self):
        event = make_event(command="API_KEY=abc123 npm start")
        result = prepare_event_for_persistence(event, PrivacyMode.STANDARD)
        self.assertNotIn("abc123", result.payload["command"])
        self.assertIn("npm start", result.payload["command"])

    def test_debug_leaves_payload_untouched(self):
        event = make_event(command="API_KEY=abc123 npm start")
        result = prepare_event_for_persistence(event, PrivacyMode.DEBUG)
        self.assertEqual(result.payload["command"], "API_KEY=abc123 npm start")

    def test_original_event_is_not_mutated(self):
        event = make_event(command="API_KEY=abc123 npm start")
        prepare_event_for_persistence(event, PrivacyMode.STRICT)
        self.assertEqual(event.payload["command"], "API_KEY=abc123 npm start")


class TestPrepareContextForPersistence(unittest.TestCase):
    def _context(self):
        return SessionContext(
            agent="claude-code",
            current_state=AgentState.ERROR,
            task="usar TOKEN=segredo-xyz no deploy",
            modified_files=["a.py"],
            tests_passed=1,
            tests_failed=1,
            recent_errors=["falha com PASSWORD=hunter2"],
        )

    def test_strict_clears_task_and_errors(self):
        result = prepare_context_for_persistence(self._context(), PrivacyMode.STRICT)
        self.assertIsNone(result.task)
        self.assertEqual(result.recent_errors, [])
        # o resto do contexto nao e texto livre, fica intacto
        self.assertEqual(result.modified_files, ["a.py"])

    def test_standard_redacts_task_and_errors(self):
        result = prepare_context_for_persistence(self._context(), PrivacyMode.STANDARD)
        self.assertNotIn("segredo-xyz", result.task)
        self.assertNotIn("hunter2", result.recent_errors[0])

    def test_debug_leaves_context_untouched(self):
        context = self._context()
        result = prepare_context_for_persistence(context, PrivacyMode.DEBUG)
        self.assertEqual(result.task, context.task)
        self.assertEqual(result.recent_errors, context.recent_errors)

    def test_strict_with_no_task_stays_none(self):
        context = self._context()
        context.task = None
        result = prepare_context_for_persistence(context, PrivacyMode.STANDARD)
        self.assertIsNone(result.task)


if __name__ == "__main__":
    unittest.main()
