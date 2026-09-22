import unittest

from pydantic import ValidationError

from visual_harness.humanization.expressions import Expression
from visual_harness.humanization.gestures import Gesture
from visual_harness.humanization.messages import check_message
from visual_harness.humanization.models import HumanizedState


class TestCheckMessage(unittest.TestCase):
    def test_none_is_allowed(self):
        check_message(None)  # não levanta

    def test_observable_phrasing_is_allowed(self):
        check_message("Vou reconsiderar essa abordagem.")  # não levanta

    def test_fear_claim_is_rejected(self):
        with self.assertRaises(ValueError):
            check_message("A IA está com medo do resultado.")

    def test_consciousness_claim_is_rejected(self):
        with self.assertRaises(ValueError):
            check_message("O agente está consciente do erro.")


class TestHumanizedStateVocabularyGuard(unittest.TestCase):
    def test_forbidden_message_rejected_at_model_level(self):
        with self.assertRaises(ValidationError):
            HumanizedState(
                expression=Expression.CONCERNED,
                gesture=Gesture.PAUSE,
                animation="error",
                message="A IA está com raiva do teste que falhou.",
            )

    def test_allowed_message_passes_at_model_level(self):
        state = HumanizedState(
            expression=Expression.THOUGHTFUL,
            gesture=Gesture.LOOK_UP,
            animation="slow_pause",
            message="Vou reconsiderar essa abordagem.",
        )
        self.assertEqual(state.message, "Vou reconsiderar essa abordagem.")


if __name__ == "__main__":
    unittest.main()
