"""E2E (Step 18, TechSpecs Seção 18-19): sessão que já tinha história
ANTES do `vh watch` conectar aparece no modo full assim que conecta,
sem nenhum evento novo precisar acontecer depois.
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
from visual_harness.terminal.renderer import MODE_FULL, TerminalOverlay


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


class TestFullModeHydratesPriorHistoryOnConnect(unittest.IsolatedAsyncioTestCase):
    async def test_context_and_timeline_from_before_the_connection_are_rendered(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                # historia acontece ANTES do vh watch existir, via REST puro
                async with httpx.AsyncClient() as http:
                    base = f"http://{server.host}:{server.port}"
                    await http.post(
                        f"{base}/api/events",
                        json={
                            "session_id": "s1",
                            "source": "claude-code",
                            "type": "task_started",
                            "payload": {"description": "corrigir login"},
                        },
                    )
                    await http.post(
                        f"{base}/api/events",
                        json={
                            "session_id": "s1",
                            "source": "claude-code",
                            "type": "test_failed",
                            "payload": {"test": "login"},
                        },
                    )

                stream = io.StringIO()
                overlay = TerminalOverlay(stream=stream, mode=MODE_FULL, rows=30)
                overlay.start()
                client_task = asyncio.ensure_future(
                    run_terminal_client(server.host, server.port, overlay)
                )
                try:
                    # nao publica NENHUM evento novo: so a hidratacao explica
                    # o que vai aparecer no stream.
                    deadline = time.monotonic() + 5
                    while "corrigir login" not in stream.getvalue():
                        if time.monotonic() > deadline:
                            self.fail(f"nunca hidratou: {stream.getvalue()!r}")
                        await asyncio.sleep(0.05)

                    output = stream.getvalue()
                    self.assertIn("corrigir login", output)
                    self.assertIn("Understanding", output)
                finally:
                    client_task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await client_task
                    overlay.stop()
            finally:
                server.stop()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
