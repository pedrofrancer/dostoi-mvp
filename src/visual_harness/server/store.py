"""Armazenamento de sessão em memória (TechSpecs Seção 17). Limitado de
propósito (a própria Seção 17 pede isso: não manter eventos ilimitados
em RAM); persistência de verdade chega no Step 11.
"""
from collections import deque
from datetime import datetime

from pydantic import BaseModel

from visual_harness.events.models import Event
from visual_harness.state.engine import derive_state
from visual_harness.state.models import AgentState

MAX_EVENTS_PER_SESSION = 1000


class SessionRecord(BaseModel):
    id: str
    agent: str
    started_at: datetime
    ended_at: datetime | None = None


class SessionStore:
    def __init__(self, max_events_per_session: int = MAX_EVENTS_PER_SESSION) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._events: dict[str, deque] = {}
        self._max_events = max_events_per_session

    def record(self, event: Event) -> None:
        session_id = event.session_id
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionRecord(
                id=session_id, agent=event.source, started_at=event.timestamp
            )
            self._events[session_id] = deque(maxlen=self._max_events)
        self._events[session_id].append(event)

    def get_session(self, session_id: str) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[SessionRecord]:
        return list(self._sessions.values())

    def get_events(self, session_id: str) -> list[Event]:
        return list(self._events.get(session_id, []))

    def current_state(self, session_id: str) -> AgentState:
        return derive_state(self.get_events(session_id))
