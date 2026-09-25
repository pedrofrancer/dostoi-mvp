"""E2E (TechSpecs Seção 32): o overlay de terminal é só mais um cliente
do `/ws` real, o mesmo protocolo que o browser antigo consumia. Sobe um
backend de verdade, roda `terminal.client.run` de verdade contra ele
(socket real), e confere que o `state_update` chega e é desenhado na
região reservada (capturada num stream em memória, não no terminal de
verdade).
"""
import asyncio
import io
import socket
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.persistence.database import create_engine_for
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore
from visual_harness.terminal.client import run as run_terminal_client
from visual_harness.terminal.renderer import TerminalOverlay


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _LiveServer:
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


class TestTerminalOverlayAgainstALiveServer(unittest.IsolatedAsyncioTestCase):
    async def test_state_update_from_a_real_event_reaches_the_overlay(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            stream = io.StringIO()
            overlay = TerminalOverlay(stream=stream, rows=24)
            overlay.start()
            client_task = asyncio.ensure_future(
                run_terminal_client(server.host, server.port, overlay)
            )
            try:
                async with httpx.AsyncClient() as http:
                    response = await http.post(
                        f"http://{server.host}:{server.port}/api/events",
                        json={
                            "session_id": "e2e-terminal",
                            "source": "cli",
                            "type": "file_read",
                            "payload": {"path": "src/e2e.py"},
                        },
                        timeout=5.0,
                    )
                self.assertEqual(response.status_code, 200)

                deadline = time.monotonic() + 5
                while "READING" not in stream.getvalue().upper():
                    if time.monotonic() > deadline:
                        self.fail(f"overlay nunca desenhou o estado: {stream.getvalue()!r}")
                    await asyncio.sleep(0.05)
            finally:
                client_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await client_task
                overlay.stop()
                server.stop()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
