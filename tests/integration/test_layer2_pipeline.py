"""Integração (TechSpecs Seção 60.1): um checkpoint de verdade dispara o
julgamento de Camada 2 e chega pelo WebSocket como `layer2_update`, sem
chave de LLM configurada (fallback determinístico, sem rede).
"""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.persistence.database import create_engine_for
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore


_PROVIDER_VARS = ("VH_JUDGE_BASE_URL", "VH_JUDGE_API_KEY", "VH_JUDGE_MODEL")


class TestLayer2PipelineOverWebSocket(unittest.TestCase):
    def setUp(self):
        self._saved = {name: os.environ.pop(name, None) for name in _PROVIDER_VARS}

    def tearDown(self):
        for name, value in self._saved.items():
            if value is not None:
                os.environ[name] = value

    def test_command_failure_broadcasts_a_layer2_update(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            try:
                bus = EventBus()
                store = SessionStore(engine=engine)
                demo_player = DemoPlayer(bus)
                app = create_app(bus, store, demo_player)
                client = TestClient(app)

                with client.websocket_connect("/ws") as websocket:
                    response = client.post(
                        "/api/events",
                        json={
                            "session_id": "s1",
                            "source": "cli",
                            "type": "command_failed",
                            "payload": {"command": "pytest"},
                        },
                    )
                    self.assertEqual(response.status_code, 200)

                    received = []
                    while True:
                        message = websocket.receive_json()
                        received.append(message)
                        if message["type"] == "layer2_update":
                            break

                layer2 = received[-1]
                self.assertEqual(layer2["payload"]["session_id"], "s1")
                self.assertEqual(layer2["payload"]["checkpoint_type"], "test_failure")
                self.assertEqual(layer2["payload"]["source"], "heuristica")
                self.assertIn("pytest", layer2["payload"]["message"])
            finally:
                engine.dispose()

    def test_command_finished_does_not_broadcast_a_layer2_update(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            try:
                bus = EventBus()
                store = SessionStore(engine=engine)
                demo_player = DemoPlayer(bus)
                app = create_app(bus, store, demo_player)
                client = TestClient(app)

                with client.websocket_connect("/ws") as websocket:
                    response = client.post(
                        "/api/events",
                        json={
                            "session_id": "s1",
                            "source": "cli",
                            "type": "command_finished",
                            "payload": {"command": "pytest"},
                        },
                    )
                    self.assertEqual(response.status_code, 200)

                    received = []
                    while True:
                        message = websocket.receive_json()
                        received.append(message)
                        if message["type"] == "state_update":
                            break

                self.assertFalse(any(m["type"] == "layer2_update" for m in received))
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
