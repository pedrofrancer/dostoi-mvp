import unittest

from visual_harness.state.models import AgentState
from visual_harness.state.transitions import arbitrate


class TestArbitrate(unittest.TestCase):
    def test_no_candidates_is_unknown(self):
        self.assertEqual(arbitrate([]), AgentState.UNKNOWN)

    def test_single_candidate_wins(self):
        self.assertEqual(arbitrate([AgentState.READING]), AgentState.READING)

    def test_waiting_beats_reading(self):
        result = arbitrate([AgentState.READING, AgentState.WAITING])
        self.assertEqual(result, AgentState.WAITING)

    def test_error_beats_success(self):
        result = arbitrate([AgentState.SUCCESS, AgentState.ERROR])
        self.assertEqual(result, AgentState.ERROR)

    def test_idle_beats_unknown(self):
        result = arbitrate([AgentState.UNKNOWN, AgentState.IDLE])
        self.assertEqual(result, AgentState.IDLE)

    def test_unknown_wins_only_when_alone(self):
        self.assertEqual(arbitrate([AgentState.UNKNOWN]), AgentState.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
