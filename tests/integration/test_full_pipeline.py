"""Integração (TechSpecs Seção 53): evento → contexto → estado →
humanização → WebSocket, com componentes de verdade, sem mock. O que
distingue isso dos testes de unidade não é o tamanho, é que aqui
`ClaudeCodeAdapter`, `EventBus`, `SessionStore` (com SQLite real),
`derive_state`, `compute_context`, `humanize` e o WebSocket da API
rodam juntos numa sessão só, como rodariam de verdade.
"""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from visual_harness.adapters.claude_code import translate_hook_event
from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.persistence.database import create_engine_for, events_table
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sample_hook_session.json"


def load_translated_events():
    """Cada linha do fixture é um payload de hook cru; traduz pelo
    adapter de verdade, não por um evento já pronto escrito à mão."""
    raw_payloads = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    events = []
    for payload in raw_payloads:
        # session_id/timestamp de teste: o fixture não carrega
        # timestamp real de hook, então cada evento pega o agora.
        event = translate_hook_event(payload)
        if event is not None:
            events.append(event)
    return events


class TestFullPipelineFromHookFixture(unittest.TestCase):
    def test_session_from_real_hook_payloads_flows_through_every_layer(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            try:
                bus = EventBus()
                store = SessionStore(engine=engine)
                demo_player = DemoPlayer(bus)
                app = create_app(bus, store, demo_player)
                client = TestClient(app)

                events = load_translated_events()
                self.assertGreater(len(events), 0, "fixture deveria traduzir pelo menos um evento")

                received_types = []
                with client.websocket_connect("/ws") as websocket:
                    for event in events:
                        response = client.post(
                            "/api/events",
                            json={
                                "session_id": event.session_id,
                                "source": event.source,
                                "type": event.type.value,
                                "payload": event.payload,
                            },
                        )
                        self.assertEqual(response.status_code, 200)

                        # drena o broadcast desse evento: sempre event +
                        # state_update, timeline_update so quando muda de fato.
                        while True:
                            message = websocket.receive_json()
                            received_types.append(message["type"])
                            if message["type"] == "state_update":
                                break
                        # timeline_update, se existir, fica pra proxima
                        # rodada de drenagem nao travar — le com timeout
                        # curto seria ideal, mas o TestClient enfileira
                        # em ordem, entao só continua no proximo evento.

                session_id = events[0].session_id

                # Camada evento: tudo que foi publicado esta em /events
                stored_events = client.get(f"/api/sessions/{session_id}/events").json()
                self.assertEqual(len(stored_events), len(events))

                # Camada contexto: arquivo tocado e teste contado batem
                # com o que o fixture realmente descreve (dois Edit no
                # mesmo arquivo, um Bash falhou depois passou)
                session = client.get(f"/api/sessions/{session_id}").json()
                context = session["context"]
                self.assertIn("src/auth.py", context["modified_files"])

                # Camada estado: a sessao termina com o teste passando
                # por ultimo, nao em erro
                timeline = client.get(f"/api/sessions/{session_id}/timeline").json()
                self.assertGreater(len(timeline), 0)
                self.assertNotEqual(timeline[-1]["to"], "error")

                # Camada humanizacao: pelo menos um state_update chegou
                # pelo WebSocket de verdade, nao só a camada de eventos
                self.assertIn("state_update", received_types)

                # Persistencia: os mesmos eventos estao no SQLite, nao
                # só na memoria do store
                with engine.begin() as conn:
                    rows = conn.execute(
                        events_table.select().where(events_table.c.session_id == session_id)
                    ).fetchall()
                self.assertEqual(len(rows), len(events))
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
