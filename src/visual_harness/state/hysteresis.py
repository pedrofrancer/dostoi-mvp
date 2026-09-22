"""Histerese de estado (TechSpecs Seção 25): evita que o estado visível
oscile rápido demais entre eventos de alta frequência. Janela sugerida
na Seção 25 é 150-300ms; 200ms como padrão fica no meio.
"""
import time
from typing import Callable

from visual_harness.state.models import AgentState


class StateHysteresis:
    def __init__(
        self,
        min_duration_ms: int = 200,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._min_duration_s = min_duration_ms / 1000
        self._clock = clock
        self._current: AgentState | None = None
        self._changed_at: float | None = None

    def update(self, candidate: AgentState) -> AgentState:
        now = self._clock()

        if self._current is None:
            self._current = candidate
            self._changed_at = now
            return self._current

        if candidate == self._current:
            return self._current

        if now - self._changed_at >= self._min_duration_s:
            self._current = candidate
            self._changed_at = now

        return self._current
