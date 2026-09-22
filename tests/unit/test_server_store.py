import unittest

from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.server.store import SessionStore
from visual_harness.state.models import AgentState


def ev(event_type, **payload):
    return Event(session_id="sess_1", source="claude-code", type=event_type, payload=payload)


class TestSessionStoreTimeline(unittest.TestCase):
    def test_first_event_creates_a_transition_from_none(self):
        store = SessionStore()
        transition = store.record(ev(EventType.TASK_STARTED, description="algo"))
        self.assertIsNotNone(transition)
        self.assertIsNone(transition.from_state)
        self.assertEqual(transition.to, AgentState.UNDERSTANDING)

    def test_event_without_state_change_returns_none_and_no_new_entry(self):
        store = SessionStore()
        store.record(ev(EventType.TASK_STARTED, description="algo"))
        # outro TASK_STARTED nao muda o estado (ja esta UNDERSTANDING)
        transition = store.record(ev(EventType.TASK_STARTED, description="algo de novo"))
        self.assertIsNone(transition)
        self.assertEqual(len(store.get_timeline("sess_1")), 1)

    def test_timeline_accumulates_across_real_transitions(self):
        store = SessionStore()
        store.record(ev(EventType.TASK_STARTED, description="algo"))
        store.record(ev(EventType.TEST_FAILED, test="login"))
        store.record(ev(EventType.APPROACH_CHANGED))

        timeline = store.get_timeline("sess_1")
        self.assertEqual(
            [(t.from_state, t.to) for t in timeline],
            [
                (None, AgentState.UNDERSTANDING),
                (AgentState.UNDERSTANDING, AgentState.ERROR),
                (AgentState.ERROR, AgentState.RECONSIDERING),
            ],
        )

    def test_get_timeline_for_unknown_session_is_empty(self):
        store = SessionStore()
        self.assertEqual(store.get_timeline("nao-existe"), [])

    def test_get_context_reflects_recorded_events(self):
        store = SessionStore()
        store.record(ev(EventType.TASK_STARTED, description="Implementar X"))
        store.record(ev(EventType.FILE_MODIFIED, path="a.py"))

        context = store.get_context("sess_1")
        self.assertIsNotNone(context)
        self.assertEqual(context.task, "Implementar X")
        self.assertEqual(context.modified_files, ["a.py"])
        self.assertEqual(context.agent, "claude-code")

    def test_get_context_for_unknown_session_is_none(self):
        store = SessionStore()
        self.assertIsNone(store.get_context("nao-existe"))


if __name__ == "__main__":
    unittest.main()
