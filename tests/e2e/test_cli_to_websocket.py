"""E2E (TechSpecs Seção 53): CLI de verdade → backend de verdade, sobre
socket real. O que distingue isso do teste de integração não é o pipeline
(já coberto), é a fronteira: `vh event`/`vh status` fazem HTTP de verdade
contra um uvicorn real numa porta real, e o WebSocket é o cliente
`websockets` de verdade — não o transporte in-process do TestClient. A
camada "browser UI/avatar" fica pra receita manual: aqui provamos que tudo
que o browser consumiria já chegou certo no fio.
"""
import asyncio
import json
import socket
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
import websockets
from typer.testing import CliRunner

from visual_harness.cli.commands import app as cli_app
from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.persistence.database import create_engine_for
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore

runner = CliRunner()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _LiveServer:
    """Backend real, num socket real, numa daemon thread."""

    def __init__(self, engine):
        self.host = "127.0.0.1"
        self.port = _free_port()
        bus = EventBus()
        store = SessionStore(engine=engine)
        demo_player = DemoPlayer(bus)
        app = create_app(bus, store, demo_player)
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def start(self) -> None:
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("servidor real não subiu a tempo")
            time.sleep(0.02)

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)


class TestCliToWebSocketOverRealSockets(unittest.TestCase):
    def test_vh_status_reaches_a_live_server(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                result = runner.invoke(
                    cli_app, ["status", "--host", server.host, "--port", str(server.port)]
                )
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("rodando", result.output)
            finally:
                server.stop()
                engine.dispose()

    def test_vh_event_reaches_backend_and_broadcasts_over_real_websocket(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                async def send_and_receive():
                    uri = f"ws://{server.host}:{server.port}/ws"
                    async with websockets.connect(uri) as websocket:
                        invoke_result = runner.invoke(
                            cli_app,
                            [
                                "event",
                                "--type", "file_read",
                                "--session", "e2e-1",
                                "--path", "src/e2e.py",
                                "--host", server.host,
                                "--port", str(server.port),
                            ],
                        )
                        self.assertEqual(invoke_result.exit_code, 0, invoke_result.output)

                        received = []
                        while True:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5)
                            received.append(json.loads(message))
                            if received[-1]["type"] == "state_update":
                                break
                        return received

                received = asyncio.run(send_and_receive())
                self.assertTrue(any(m["type"] == "event" for m in received))
                self.assertTrue(any(m["type"] == "state_update" for m in received))
            finally:
                server.stop()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
