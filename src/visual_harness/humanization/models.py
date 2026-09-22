"""Estado humanizado (TechSpecs Seção 26): tradução visual do estado
operacional bruto.
"""
from pydantic import BaseModel, Field, field_validator

from visual_harness.humanization.expressions import Expression
from visual_harness.humanization.gestures import Gesture
from visual_harness.humanization.messages import check_message


class HumanizedState(BaseModel):
    expression: Expression
    gesture: Gesture
    animation: str
    intensity: float = Field(ge=0.0, le=1.0, default=0.5)
    message: str | None = None
    duration_ms: int = 1000

    @field_validator("message")
    @classmethod
    def _message_follows_vocabulary(cls, value: str | None) -> str | None:
        check_message(value)
        return value
