"""Esquema SQLite (TechSpecs Seção 18, 49): sessions, events,
state_transitions, context_snapshots. SQLAlchemy Core, não ORM: as
tabelas batem quase literal com os `CREATE TABLE` do TechSpecs, um ORM
completo só adicionaria indireção sem comprar nada aqui.
"""
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

sessions_table = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("agent", String, nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("ended_at", DateTime, nullable=True),
)

events_table = Table(
    "events",
    metadata,
    Column("id", String, primary_key=True),
    Column("session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("source", String, nullable=False),
    Column("type", String, nullable=False),
    Column("version", Integer, nullable=False),
    # Nunca o terminal bruto (Seção 49): só o payload já estruturado do
    # Event, que por desenho (Step 2) nunca carrega stdout cru.
    Column("payload_json", Text, nullable=False),
    Index("idx_events_session_sequence", "session_id", "sequence"),
)

state_transitions_table = Table(
    "state_transitions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("from_state", String, nullable=True),
    Column("to_state", String, nullable=False),
    Column("trigger", String, nullable=False),
    Column("confidence", Float, nullable=False),
)

context_snapshots_table = Table(
    "context_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("context_json", Text, nullable=False),
)


def create_engine_for(path: Path) -> Engine:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    metadata.create_all(engine)
    return engine
