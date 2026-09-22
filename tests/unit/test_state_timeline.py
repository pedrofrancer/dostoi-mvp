import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from visual_harness.state.models import AgentState
from visual_harness.state.timeline import StateTransition


class TestStateTransition(unittest.TestCase):
    def test_from_field_uses_alias_in_json(self):
        transition = StateTransition(
            timestamp=datetime.now(timezone.utc),
            from_state=AgentState.UNDERSTANDING,
            to=AgentState.ERROR,
            trigger="test_failed",
        )
        dumped = transition.model_dump(mode="json", by_alias=True)
        self.assertEqual(dumped["from"], "understanding")
        self.assertNotIn("from_state", dumped)

    def test_from_state_defaults_to_none(self):
        transition = StateTransition(
            timestamp=datetime.now(timezone.utc),
            to=AgentState.UNDERSTANDING,
            trigger="task_started",
        )
        self.assertIsNone(transition.from_state)

    def test_confidence_defaults_to_one(self):
        transition = StateTransition(
            timestamp=datetime.now(timezone.utc),
            to=AgentState.UNDERSTANDING,
            trigger="task_started",
        )
        self.assertEqual(transition.confidence, 1.0)

    def test_confidence_out_of_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            StateTransition(
                timestamp=datetime.now(timezone.utc),
                to=AgentState.UNDERSTANDING,
                trigger="task_started",
                confidence=1.5,
            )

    def test_can_construct_by_field_name_too(self):
        transition = StateTransition(
            timestamp=datetime.now(timezone.utc),
            from_state=AgentState.IDLE,
            to=AgentState.UNDERSTANDING,
            trigger="task_started",
        )
        self.assertEqual(transition.from_state, AgentState.IDLE)


if __name__ == "__main__":
    unittest.main()
