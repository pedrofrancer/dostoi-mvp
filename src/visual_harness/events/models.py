"""Modelo de evento comum (TechSpecs Seção 7): todo evento do sistema
nasce e morre neste formato, seja qual for o adapter que o gerou.
"""
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator

from visual_harness.events._uuid7 import uuid7
from visual_harness.events.types import EventType

# Seção 10 do TechSpecs (e os exemplos da Seção 52): só entram aqui os
# tipos com schema de payload explícito no documento. O resto valida
# apenas como dict, porque a Seção 50 deixa o schema completo por tipo
# como questão em aberto, não fechada ainda.
REQUIRED_PAYLOAD_FIELDS: dict[EventType, tuple[str, ...]] = {
    EventType.FILE_READ: ("path",),
    EventType.FILE_CREATED: ("path",),
    EventType.FILE_MODIFIED: ("path",),
    EventType.FILE_DELETED: ("path",),
    EventType.FILE_SEARCHED: ("path",),
    EventType.COMMAND_STARTED: ("command",),
    EventType.COMMAND_FINISHED: ("command",),
    EventType.COMMAND_FAILED: ("command",),
    EventType.TEST_FAILED: ("test",),
    EventType.TEST_SUITE_COMPLETED: ("passed", "failed"),
}


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()))
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    type: EventType
    version: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)
    sequence: int | None = None

    @model_validator(mode="after")
    def _check_required_payload_fields(self) -> "Event":
        required = REQUIRED_PAYLOAD_FIELDS.get(self.type)
        if required:
            missing = [field for field in required if field not in self.payload]
            if missing:
                raise ValueError(
                    f"evento {self.type.value} exige payload com {missing}"
                )
        return self
