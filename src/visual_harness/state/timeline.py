"""Registro de transição de estado (TechSpecs Seção 65): cada mudança de
estado ao longo de uma sessão vira uma entrada replayável, não algo
recalculado do zero a cada consulta.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from visual_harness.state.models import AgentState


class StateTransition(BaseModel):
    timestamp: datetime
    from_state: AgentState | None = Field(default=None, alias="from")
    to: AgentState
    trigger: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

    model_config = {"populate_by_name": True}
