"""Ponto de entrada do backend (TechSpecs Seção 5, 38, 42). Bind padrão
em 127.0.0.1: nunca 0.0.0.0 por padrão, mesmo que isso custe a
comodidade de testar de outro dispositivo na rede sem mudar a flag.
"""
from pathlib import Path

import uvicorn

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def build_app():
    bus = EventBus()
    store = SessionStore()
    demo_player = DemoPlayer(bus)
    return create_app(bus, store, demo_player, static_dir=FRONTEND_DIR)


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    uvicorn.run(build_app(), host=host, port=port)


if __name__ == "__main__":
    run()
