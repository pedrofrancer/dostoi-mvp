import unittest

from pydantic import ValidationError

from visual_harness.state.models import AgentState, StateEstimate


class TestStateEstimate(unittest.TestCase):
    def test_defaults(self):
        estimate = StateEstimate(state=AgentState.IDLE)
        self.assertEqual(estimate.confidence, 1.0)
        self.assertEqual(estimate.basis, [])
        self.assertFalse(estimate.observed)

    def test_confidence_above_one_is_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(state=AgentState.IDLE, confidence=1.5)

    def test_confidence_below_zero_is_rejected(self):
        with self.assertRaises(ValidationError):
            StateEstimate(state=AgentState.IDLE, confidence=-0.1)

    def test_carries_basis_and_observed(self):
        estimate = StateEstimate(
            state=AgentState.ERROR,
            confidence=0.9,
            basis=["test_failed"],
            observed=True,
        )
        self.assertEqual(estimate.basis, ["test_failed"])
        self.assertTrue(estimate.observed)


if __name__ == "__main__":
    unittest.main()
