"""Julgamento de Camada 2 pronto pra sair pelo WebSocket (TechSpecs
Seção 60.1, 33). Fora de `humanization/` de propósito: aquele módulo só
mapeia `AgentState -> HumanizedState`, nunca julga o código em si
(Seção 60.1).
"""
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from visual_harness.humanization.messages import check_message


class Layer2Judgment(BaseModel):
    session_id: str
    checkpoint_type: str
    message: str
    source: str  # "llm" ou "heuristica"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("message")
    @classmethod
    def _message_follows_vocabulary(cls, value: str) -> str:
        check_message(value)
        return value
