"""Estado do agente e sua estimativa (TechSpecs Seção 21-22)."""
from enum import Enum

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    IDLE = "idle"
    UNDERSTANDING = "understanding"
    EXPLORING = "exploring"
    THINKING = "thinking"
    PLANNING = "planning"
    READING = "reading"
    WRITING = "writing"
    EXECUTING = "executing"
    TESTING = "testing"
    INVESTIGATING = "investigating"
    RECONSIDERING = "reconsidering"
    BLOCKED = "blocked"
    WAITING = "waiting"
    RECOVERING = "recovering"
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"


class StateEstimate(BaseModel):
    state: AgentState
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    basis: list[str] = Field(default_factory=list)
    observed: bool = False
