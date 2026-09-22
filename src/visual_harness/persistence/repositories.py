"""Leitura/escrita sobre as tabelas de `database.py`. Fino de propósito:
quem decide O QUE persistir é o `SessionStore`; isso aqui só grava e lê
linha, sem lógica de negócio.
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from visual_harness.context.models import SessionContext
from visual_harness.events.models import Event
from visual_harness.persistence.database import (
    context_snapshots_table,
    events_table,
    sessions_table,
    state_transitions_table,
)
from visual_harness.state.timeline import StateTransition


def save_session(engine: Engine, session_id: str, agent: str, started_at: datetime) -> None:
    with engine.begin() as conn:
        exists = conn.execute(
            select(sessions_table.c.id).where(sessions_table.c.id == session_id)
        ).first()
        if exists:
            return
        conn.execute(
            insert(sessions_table).values(id=session_id, agent=agent, started_at=started_at)
        )


def save_event(engine: Engine, event: Event) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(events_table).values(
                id=event.id,
                session_id=event.session_id,
                sequence=event.sequence or 0,
                timestamp=event.timestamp,
                source=event.source,
                type=event.type.value,
                version=event.version,
                payload_json=json.dumps(event.payload),
            )
        )


def save_transition(engine: Engine, session_id: str, transition: StateTransition) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(state_transitions_table).values(
                session_id=session_id,
                timestamp=transition.timestamp,
                from_state=transition.from_state.value if transition.from_state else None,
                to_state=transition.to.value,
                trigger=transition.trigger,
                confidence=transition.confidence,
            )
        )


def save_context_snapshot(engine: Engine, session_id: str, context: SessionContext) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(context_snapshots_table).values(
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
                context_json=context.model_dump_json(),
            )
        )


def get_events(engine: Engine, session_id: str) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(events_table)
            .where(events_table.c.session_id == session_id)
            .order_by(events_table.c.sequence)
        ).mappings()
        return [dict(row) for row in rows]


def get_transitions(engine: Engine, session_id: str) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(state_transitions_table)
            .where(state_transitions_table.c.session_id == session_id)
            .order_by(state_transitions_table.c.id)
        ).mappings()
        return [dict(row) for row in rows]


def purge_older_than(engine: Engine, retention_days: int) -> int:
    """Apaga eventos com mais de `retention_days` (Seção 50). Não é
    chamado automaticamente em lugar nenhum ainda: `vh sessions purge`
    continua Future Work explícito no TechSpecs (Seção 50)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    with engine.begin() as conn:
        result = conn.execute(delete(events_table).where(events_table.c.timestamp < cutoff))
        return result.rowcount
