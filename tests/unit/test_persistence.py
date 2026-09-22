import json
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from visual_harness.context.engine import compute_context
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.persistence import repositories
from visual_harness.persistence.database import (
    context_snapshots_table,
    create_engine_for,
    events_table,
    sessions_table,
    state_transitions_table,
)
from visual_harness.state.models import AgentState
from visual_harness.state.timeline import StateTransition


def ev(event_type, sequence=1, **payload):
    event = Event(session_id="sess_1", source="claude-code", type=event_type, payload=payload)
    event.sequence = sequence
    return event


@contextmanager
def temp_engine():
    """SQLite no Windows não deixa apagar o arquivo com a conexão ainda
    aberta; engine.dispose() antes do TemporaryDirectory tentar limpar."""
    with TemporaryDirectory() as tmp:
        engine = create_engine_for(Path(tmp) / "harness.db")
        try:
            yield engine
        finally:
            engine.dispose()


class TestCreateEngineFor(unittest.TestCase):
    def test_creates_all_four_tables(self):
        with temp_engine() as engine:
            with engine.connect() as conn:
                table_names = set(engine.dialect.get_table_names(conn))
            self.assertEqual(
                table_names,
                {"sessions", "events", "state_transitions", "context_snapshots"},
            )


class TestRepositories(unittest.TestCase):
    def test_save_session_is_idempotent(self):
        with temp_engine() as engine:
            now = datetime.now(timezone.utc)
            repositories.save_session(engine, "sess_1", "claude-code", now)
            repositories.save_session(engine, "sess_1", "claude-code", now)

            with engine.begin() as conn:
                rows = conn.execute(sessions_table.select()).fetchall()
            self.assertEqual(len(rows), 1)

    def test_save_event_persists_payload_as_json(self):
        with temp_engine() as engine:
            event = ev(EventType.FILE_READ, path="src/main.py")
            repositories.save_event(engine, event)

            events = repositories.get_events(engine, "sess_1")
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(events[0]["payload_json"]), {"path": "src/main.py"})

    def test_get_events_ordered_by_sequence(self):
        with temp_engine() as engine:
            repositories.save_event(engine, ev(EventType.TASK_STARTED, sequence=2))
            repositories.save_event(engine, ev(EventType.AGENT_WAITING, sequence=1))

            events = repositories.get_events(engine, "sess_1")
            self.assertEqual([e["sequence"] for e in events], [1, 2])

    def test_save_and_get_transition(self):
        with temp_engine() as engine:
            transition = StateTransition(
                timestamp=datetime.now(timezone.utc),
                from_state=AgentState.UNDERSTANDING,
                to=AgentState.ERROR,
                trigger="test_failed",
            )
            repositories.save_transition(engine, "sess_1", transition)

            rows = repositories.get_transitions(engine, "sess_1")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["from_state"], "understanding")
            self.assertEqual(rows[0]["to_state"], "error")

    def test_save_context_snapshot(self):
        with temp_engine() as engine:
            context = compute_context(
                [ev(EventType.TASK_STARTED, description="algo")], "claude-code"
            )
            repositories.save_context_snapshot(engine, "sess_1", context)

            with engine.begin() as conn:
                rows = conn.execute(context_snapshots_table.select()).mappings().all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(json.loads(rows[0]["context_json"])["task"], "algo")

    def test_purge_older_than_removes_old_events_only(self):
        with temp_engine() as engine:
            old_event = ev(EventType.TASK_STARTED, sequence=1)
            old_event.timestamp = datetime.now(timezone.utc) - timedelta(days=40)
            recent_event = ev(EventType.TASK_STARTED, sequence=2)

            repositories.save_event(engine, old_event)
            repositories.save_event(engine, recent_event)

            removed = repositories.purge_older_than(engine, retention_days=30)

            self.assertEqual(removed, 1)
            remaining = repositories.get_events(engine, "sess_1")
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0]["id"], recent_event.id)


class TestSessionStoreWithPersistence(unittest.TestCase):
    def test_record_writes_through_to_sqlite(self):
        from visual_harness.server.store import SessionStore

        with temp_engine() as engine:
            store = SessionStore(engine=engine)

            store.record(ev(EventType.TASK_STARTED, sequence=1, description="algo"))
            store.record(ev(EventType.TEST_FAILED, sequence=2, test="login"))

            with engine.begin() as conn:
                event_rows = conn.execute(events_table.select()).fetchall()
                transition_rows = conn.execute(state_transitions_table.select()).fetchall()
                snapshot_rows = conn.execute(context_snapshots_table.select()).fetchall()

            self.assertEqual(len(event_rows), 2)
            self.assertEqual(len(transition_rows), 2)
            self.assertEqual(len(snapshot_rows), 2)

    def test_privacy_mode_redacts_persisted_payload_but_not_in_memory(self):
        import json

        from visual_harness.privacy.modes import PrivacyMode
        from visual_harness.server.store import SessionStore

        with temp_engine() as engine:
            store = SessionStore(engine=engine, privacy_mode=PrivacyMode.STANDARD)
            event = ev(EventType.COMMAND_STARTED, sequence=1, command="API_KEY=abc123 npm start")
            store.record(event)

            in_memory = store.get_events("sess_1")[0]
            self.assertEqual(in_memory.payload["command"], "API_KEY=abc123 npm start")

            with engine.begin() as conn:
                row = conn.execute(events_table.select()).mappings().first()
            persisted_payload = json.loads(row["payload_json"])
            self.assertNotIn("abc123", persisted_payload["command"])

    def test_record_without_engine_touches_no_sqlite(self):
        from visual_harness.server.store import SessionStore

        store = SessionStore()  # engine=None, o padrão de todos os testes até aqui
        transition = store.record(ev(EventType.TASK_STARTED, sequence=1))
        self.assertIsNotNone(transition)  # continua funcionando em memória


if __name__ == "__main__":
    unittest.main()
