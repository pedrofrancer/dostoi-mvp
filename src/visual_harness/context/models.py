"""Modelo de contexto de sessão (TechSpecs Seção 19, painel da Seção
64). Um resumo do que já aconteceu, não um registro evento a evento.
"""
from pydantic import BaseModel, Field

from visual_harness.state.models import AgentState


class SessionContext(BaseModel):
    agent: str
    current_state: AgentState
    task: str | None = None
    modified_files: list[str] = Field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0
    recent_errors: list[str] = Field(default_factory=list)
