"""Unidade (Step 18, TechSpecs Seção 18-19): a busca por REST do que já
existia antes da conexão, contra um backend real (REST de verdade, sem
mock de `httpx`).
"""
import unittest
from pathlib import Path
from socket import socket
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic, sleep
from unittest.mock import MagicMock

import httpx
import uvicorn

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.persistence.database import create_engine_for
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore
from visual_harness.terminal.client import discover_active_session, hydrate


def _free_port() -> int:
    with socket() as sock:
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
        self.thread = Thread(target=self.server.run, daemon=True)

    def start(self) -> None:
        self.thread.start()
        deadline = monotonic() + 5
        while not self.server.started:
            if monotonic() > deadline:
                raise RuntimeError("servidor real não subiu a tempo")
            sleep(0.02)

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)


class TestHydrateAgainstALiveServer(unittest.IsolatedAsyncioTestCase):
    async def test_hydrate_renders_existing_context_and_timeline(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                async with httpx.AsyncClient() as http:
                    await http.post(
                        f"http://{server.host}:{server.port}/api/events",
                        json={
                            "session_id": "s1",
                            "source": "claude-code",
                            "type": "task_started",
                            "payload": {"description": "corrigir login"},
                        },
                    )

                overlay = MagicMock()
                await hydrate(server.host, server.port, "s1", overlay)

                overlay.render_context.assert_called_once()
                context_call = overlay.render_context.call_args[0][0]
                self.assertEqual(context_call["session_id"], "s1")
                self.assertEqual(context_call["context"]["task"], "corrigir login")

                overlay.render_timeline_entry.assert_called_once()
                timeline_call = overlay.render_timeline_entry.call_args[0][0]
                self.assertEqual(timeline_call["transition"]["to"], "understanding")
            finally:
                server.stop()
                engine.dispose()

    async def test_hydrate_of_unknown_session_does_not_raise(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                overlay = MagicMock()
                await hydrate(server.host, server.port, "nao-existe", overlay)
                overlay.render_context.assert_not_called()
                overlay.render_timeline_entry.assert_not_called()
            finally:
                server.stop()
                engine.dispose()

    async def test_hydrate_with_server_unreachable_does_not_raise(self):
        overlay = MagicMock()
        await hydrate("127.0.0.1", 1, "s1", overlay)  # porta 1: ninguem escuta
        overlay.render_context.assert_not_called()


class TestDiscoverActiveSession(unittest.IsolatedAsyncioTestCase):
    async def test_no_sessions_returns_none(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                result = await discover_active_session(server.host, server.port)
                self.assertIsNone(result)
            finally:
                server.stop()
                engine.dispose()

    async def test_exactly_one_session_returns_its_id(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                async with httpx.AsyncClient() as http:
                    await http.post(
                        f"http://{server.host}:{server.port}/api/events",
                        json={
                            "session_id": "unica",
                            "source": "claude-code",
                            "type": "task_started",
                            "payload": {},
                        },
                    )
                result = await discover_active_session(server.host, server.port)
                self.assertEqual(result, "unica")
            finally:
                server.stop()
                engine.dispose()

    async def test_two_sessions_returns_none_ambiguous(self):
        with TemporaryDirectory() as tmp:
            engine = create_engine_for(Path(tmp) / "harness.db")
            server = _LiveServer(engine)
            server.start()
            try:
                async with httpx.AsyncClient() as http:
                    for session_id in ("a", "b"):
                        await http.post(
                            f"http://{server.host}:{server.port}/api/events",
                            json={
                                "session_id": session_id,
                                "source": "claude-code",
                                "type": "task_started",
                                "payload": {},
                            },
                        )
                result = await discover_active_session(server.host, server.port)
                self.assertIsNone(result)
            finally:
                server.stop()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
