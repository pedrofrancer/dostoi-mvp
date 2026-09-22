import unittest

from visual_harness.state.hysteresis import StateHysteresis
from visual_harness.state.models import AgentState


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def __call__(self) -> float:
        return self._now


class TestStateHysteresis(unittest.TestCase):
    def test_first_update_sets_state_immediately(self):
        clock = _FakeClock()
        hysteresis = StateHysteresis(min_duration_ms=200, clock=clock)
        self.assertEqual(hysteresis.update(AgentState.READING), AgentState.READING)

    def test_rapid_change_within_window_is_suppressed(self):
        clock = _FakeClock()
        hysteresis = StateHysteresis(min_duration_ms=200, clock=clock)
        hysteresis.update(AgentState.READING)
        clock.advance(0.05)
        self.assertEqual(hysteresis.update(AgentState.WRITING), AgentState.READING)

    def test_change_after_window_is_applied(self):
        clock = _FakeClock()
        hysteresis = StateHysteresis(min_duration_ms=200, clock=clock)
        hysteresis.update(AgentState.READING)
        clock.advance(0.25)
        self.assertEqual(hysteresis.update(AgentState.WRITING), AgentState.WRITING)

    def test_same_state_repeated_does_not_reset_timer(self):
        clock = _FakeClock()
        hysteresis = StateHysteresis(min_duration_ms=200, clock=clock)
        hysteresis.update(AgentState.READING)
        clock.advance(0.15)
        hysteresis.update(AgentState.READING)
        clock.advance(0.10)
        # 0.25s desde a primeira mudanca, mesmo em duas checagens de 0.15+0.10
        self.assertEqual(hysteresis.update(AgentState.WRITING), AgentState.WRITING)


if __name__ == "__main__":
    unittest.main()
