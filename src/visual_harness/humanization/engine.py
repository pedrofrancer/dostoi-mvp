"""Motor de humanização (TechSpecs Seção 26): estado operacional vira
comportamento visual. Cobertura dos dezessete estados; UNKNOWN cai em
neutro e sem mensagem (Seção 59: nunca fabricar).
"""
from visual_harness.humanization.expressions import Expression
from visual_harness.humanization.gestures import Gesture
from visual_harness.humanization.models import HumanizedState
from visual_harness.state.models import AgentState

_FALLBACK = HumanizedState(
    expression=Expression.NEUTRAL, gesture=Gesture.IDLE, animation="idle"
)

_STATE_MAP: dict[AgentState, HumanizedState] = {
    AgentState.IDLE: HumanizedState(
        expression=Expression.NEUTRAL, gesture=Gesture.IDLE, animation="idle"
    ),
    AgentState.UNDERSTANDING: HumanizedState(
        expression=Expression.FOCUSED,
        gesture=Gesture.LOOK_UP,
        animation="understanding",
        message="Entendendo o pedido.",
    ),
    AgentState.EXPLORING: HumanizedState(
        expression=Expression.CURIOUS, gesture=Gesture.LOOK_LEFT, animation="exploring"
    ),
    AgentState.THINKING: HumanizedState(
        expression=Expression.THOUGHTFUL, gesture=Gesture.PAUSE, animation="thinking"
    ),
    AgentState.PLANNING: HumanizedState(
        expression=Expression.FOCUSED, gesture=Gesture.LOOK_UP, animation="planning"
    ),
    AgentState.READING: HumanizedState(
        expression=Expression.FOCUSED, gesture=Gesture.IDLE, animation="reading"
    ),
    AgentState.WRITING: HumanizedState(
        expression=Expression.FOCUSED, gesture=Gesture.LEAN_FORWARD, animation="writing"
    ),
    AgentState.EXECUTING: HumanizedState(
        expression=Expression.ATTENTIVE, gesture=Gesture.IDLE, animation="executing"
    ),
    AgentState.TESTING: HumanizedState(
        expression=Expression.ATTENTIVE, gesture=Gesture.IDLE, animation="testing"
    ),
    AgentState.INVESTIGATING: HumanizedState(
        expression=Expression.CONCERNED,
        gesture=Gesture.LOOK_DOWN,
        animation="investigating",
        message="Tem alguma coisa aqui que não está fechando.",
    ),
    AgentState.RECONSIDERING: HumanizedState(
        expression=Expression.THOUGHTFUL,
        gesture=Gesture.LOOK_UP,
        animation="slow_pause",
        message="Vou reconsiderar essa abordagem.",
        intensity=0.65,
        duration_ms=1800,
    ),
    AgentState.BLOCKED: HumanizedState(
        expression=Expression.CONCERNED,
        gesture=Gesture.PAUSE,
        animation="blocked",
        message="Preciso de uma decisão sua aqui.",
    ),
    AgentState.WAITING: HumanizedState(
        expression=Expression.ATTENTIVE,
        gesture=Gesture.IDLE,
        animation="waiting",
        message="Estou esperando você.",
    ),
    AgentState.RECOVERING: HumanizedState(
        expression=Expression.RELIEVED,
        gesture=Gesture.NOD,
        animation="recovering",
        message="Agora entendi o problema.",
    ),
    AgentState.SUCCESS: HumanizedState(
        expression=Expression.SATISFIED,
        gesture=Gesture.NOD,
        animation="success",
        message="Resolvido.",
    ),
    AgentState.ERROR: HumanizedState(
        expression=Expression.CONCERNED,
        gesture=Gesture.SMALL_SHAKE,
        animation="error",
        message="Encontrei um erro.",
    ),
    AgentState.UNKNOWN: HumanizedState(
        expression=Expression.NEUTRAL, gesture=Gesture.IDLE, animation="idle"
    ),
}


def humanize(state: AgentState) -> HumanizedState:
    return _STATE_MAP.get(state, _FALLBACK).model_copy()
