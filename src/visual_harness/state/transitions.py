"""Ordem de arbitração entre estados conflitantes (TechSpecs Seção 24).
UNKNOWN é o fallback: só vence quando é o único candidato.
"""
from visual_harness.state.models import AgentState

STATE_PRIORITY: list[AgentState] = [
    AgentState.WAITING,
    AgentState.ERROR,
    AgentState.SUCCESS,
    AgentState.BLOCKED,
    AgentState.RECOVERING,
    AgentState.RECONSIDERING,
    AgentState.INVESTIGATING,
    AgentState.TESTING,
    AgentState.EXECUTING,
    AgentState.WRITING,
    AgentState.READING,
    AgentState.PLANNING,
    AgentState.THINKING,
    AgentState.EXPLORING,
    AgentState.UNDERSTANDING,
    AgentState.IDLE,
    AgentState.UNKNOWN,
]


def arbitrate(candidates: list[AgentState]) -> AgentState:
    """Dado mais de um estado candidato pro mesmo instante (vindos de
    fontes de sinal independentes), devolve o de maior prioridade."""
    for state in STATE_PRIORITY:
        if state in candidates:
            return state
    return AgentState.UNKNOWN
