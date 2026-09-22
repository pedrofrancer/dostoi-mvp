"""Rotas REST e WebSocket (TechSpecs Seção 33-34). O bind em 127.0.0.1
(Seção 42) acontece em `main.py`, não aqui; este módulo só declara o
comportamento das rotas.
"""
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from visual_harness import __version__
from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.humanization.engine import humanize
from visual_harness.server.store import SessionStore
from visual_harness.state.engine import derive_state
from visual_harness.state.models import AgentState


class EventIn(BaseModel):
    session_id: str
    source: str
    type: EventType
    payload: dict = {}


def create_app(
    bus: EventBus,
    store: SessionStore,
    demo_player: DemoPlayer,
    static_dir: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Visual Harness")
    start_time = time.monotonic()

    async def _on_event(event: Event) -> None:
        store.record(event)

    bus.subscribe(_on_event)

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "version": __version__,
            "uptime": time.monotonic() - start_time,
            "connected_adapters": 0,
        }

    @app.get("/api/sessions")
    async def list_sessions():
        return [s.model_dump(mode="json") for s in store.list_sessions()]

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        session = store.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="sessão não encontrada")
        return session.model_dump(mode="json")

    @app.get("/api/sessions/{session_id}/events")
    async def get_session_events(session_id: str):
        if store.get_session(session_id) is None:
            raise HTTPException(status_code=404, detail="sessão não encontrada")
        return [e.model_dump(mode="json") for e in store.get_events(session_id)]

    @app.get("/api/sessions/{session_id}/timeline")
    async def get_session_timeline(session_id: str):
        if store.get_session(session_id) is None:
            raise HTTPException(status_code=404, detail="sessão não encontrada")
        return compute_timeline(store.get_events(session_id))

    @app.post("/api/events")
    async def post_event(event_in: EventIn):
        event = Event(**event_in.model_dump())
        await bus.publish(event)
        return event.model_dump(mode="json")

    @app.post("/api/demo/start")
    async def demo_start():
        await demo_player.start()
        return {"state": demo_player.state.value}

    @app.post("/api/demo/stop")
    async def demo_stop():
        await demo_player.stop()
        return {"state": demo_player.state.value}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()

        async def forward(event: Event) -> None:
            await websocket.send_json(
                {"type": "event", "payload": event.model_dump(mode="json")}
            )
            state = derive_state(store.get_events(event.session_id))
            humanized = humanize(state)
            await websocket.send_json(
                {
                    "type": "state_update",
                    "payload": {
                        "session_id": event.session_id,
                        "state": state.value,
                        "humanization": humanized.model_dump(mode="json"),
                    },
                }
            )

        subscription = bus.subscribe(forward)
        try:
            while True:
                message = await websocket.receive_json()
                msg_type = message.get("type")
                if msg_type == "demo_start":
                    await demo_player.start()
                elif msg_type == "demo_stop":
                    await demo_player.stop()
        except WebSocketDisconnect:
            pass
        finally:
            subscription.unsubscribe()

    if static_dir is not None and static_dir.is_dir():
        # Montado por último: rotas de API sempre têm prioridade sobre
        # arquivo estático de mesmo caminho.
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")

    return app


def compute_timeline(events: list[Event]) -> list[dict]:
    """Transições de estado ao longo da sessão (TechSpecs Seção 65),
    recalculadas a partir dos eventos com o motor do Step 4. Versão
    mínima: o Step 9 é quem formaliza isso como registro persistido.
    """
    timeline: list[dict] = []
    previous_state: AgentState | None = None
    for i in range(1, len(events) + 1):
        current_state = derive_state(events[:i])
        if current_state != previous_state:
            timeline.append(
                {
                    "timestamp": events[i - 1].timestamp.isoformat(),
                    "from": previous_state.value if previous_state else None,
                    "to": current_state.value,
                    "trigger": events[i - 1].type.value,
                }
            )
            previous_state = current_state
    return timeline
