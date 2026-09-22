import unittest

from visual_harness.humanization.engine import humanize
from visual_harness.humanization.expressions import Expression
from visual_harness.humanization.gestures import Gesture
from visual_harness.state.models import AgentState


class TestHumanize(unittest.TestCase):
    """Os tres casos oficiais do TechSpecs Secao 55."""

    def test_reconsidering(self):
        result = humanize(AgentState.RECONSIDERING)
        self.assertEqual(result.expression, Expression.THOUGHTFUL)
        self.assertEqual(result.gesture, Gesture.LOOK_UP)

    def test_waiting(self):
        result = humanize(AgentState.WAITING)
        self.assertEqual(result.expression, Expression.ATTENTIVE)
        self.assertEqual(result.gesture, Gesture.IDLE)

    def test_success(self):
        result = humanize(AgentState.SUCCESS)
        self.assertIn(result.expression, (Expression.RELIEVED, Expression.SATISFIED))

    # Cobertura e garantias extras.

    def test_every_agent_state_has_a_mapping(self):
        for state in AgentState:
            result = humanize(state)
            self.assertIsInstance(result.expression, Expression)
            self.assertIsInstance(result.gesture, Gesture)

    def test_unknown_state_has_no_fabricated_message(self):
        result = humanize(AgentState.UNKNOWN)
        self.assertIsNone(result.message)
        self.assertEqual(result.expression, Expression.NEUTRAL)

    def test_returned_state_is_an_independent_copy(self):
        first = humanize(AgentState.SUCCESS)
        first.intensity = 0.0
        second = humanize(AgentState.SUCCESS)
        self.assertNotEqual(second.intensity, 0.0)


if __name__ == "__main__":
    unittest.main()
