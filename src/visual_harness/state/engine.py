"""Motor de estado: regras determinísticas (TechSpecs Seção 23) sobre
uma janela de eventos. Cada regra, na ordem escrita, pode sobrescrever o
estado decidido pelas anteriores: é a mesma semântica do pseudocódigo do
TechSpecs, uma cascata, não um match exclusivo.
"""
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.state.models import AgentState

_READ_TYPES = (EventType.FILE_READ, EventType.FILE_SEARCHED)


def derive_state(events: list[Event]) -> AgentState:
    if not events:
        return AgentState.UNKNOWN

    state = AgentState.UNKNOWN

    if any(e.type == EventType.TASK_STARTED for e in events):
        state = AgentState.UNDERSTANDING

    if any(e.type in _READ_TYPES for e in events):
        state = AgentState.READING

    test_failed_index = _last_index(events, EventType.TEST_FAILED)
    if test_failed_index is not None:
        state = AgentState.ERROR
        if any(e.type in _READ_TYPES for e in events[test_failed_index + 1 :]):
            state = AgentState.INVESTIGATING

    if any(e.type == EventType.APPROACH_CHANGED for e in events):
        state = AgentState.RECONSIDERING

    if any(e.type == EventType.AGENT_WAITING for e in events):
        state = AgentState.WAITING

    tests_ok = any(e.type == EventType.TEST_PASSED for e in events) or any(
        e.type == EventType.TEST_SUITE_COMPLETED and e.payload.get("failed") == 0
        for e in events
    )
    if tests_ok and any(e.type == EventType.AGENT_COMPLETED for e in events):
        state = AgentState.SUCCESS

    return state


def _last_index(events: list[Event], event_type: EventType) -> int | None:
    for i in range(len(events) - 1, -1, -1):
        if events[i].type == event_type:
            return i
    return None
