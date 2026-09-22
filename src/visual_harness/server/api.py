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
from visual_harness.state.hysteresis import StateHysteresis


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
    connected_websockets: set[WebSocket] = set()
    # Histerese (Step 4, Secao 25) por sessao: so afeta o que o
    # WebSocket manda pro avatar, nunca o estado "oficial" que o store
    # grava na timeline (esse continua sempre o raw, sem debounce).
    hysteresis_by_session: dict[str, StateHysteresis] = {}

    async def _broadcast(message: dict) -> None:
        dead: list[WebSocket] = []
        for websocket in connected_websockets:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            connected_websockets.discard(websocket)

    async def _on_event(event: Event) -> None:
        # Único ponto que grava no store: garante que POST /api/events
        # funcione com zero WebSocket conectado (os testes de REST
        # dependem disso), e que o broadcast nunca grave duas vezes.
        transition = store.record(event)

        await _broadcast({"type": "event", "payload": event.model_dump(mode="json")})

        raw_state = derive_state(store.get_events(event.session_id))
        hysteresis = hysteresis_by_session.setdefault(event.session_id, StateHysteresis())
        visible_state = hysteresis.update(raw_state)
        humanized = humanize(visible_state)
        await _broadcast(
            {
                "type": "state_update",
                "payload": {
                    "session_id": event.session_id,
                    "state": visible_state.value,
                    "humanization": humanized.model_dump(mode="json"),
                },
            }
        )

        if transition is not None:
            await _broadcast(
                {
                    "type": "timeline_update",
                    "payload": {
                        "session_id": event.session_id,
                        "transition": transition.model_dump(mode="json", by_alias=True),
                    },
                }
            )

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
        context = store.get_context(session_id)
        return {
            **session.model_dump(mode="json"),
            "context": context.model_dump(mode="json") if context else None,
        }

    @app.get("/api/sessions/{session_id}/events")
    async def get_session_events(session_id: str):
        if store.get_session(session_id) is None:
            raise HTTPException(status_code=404, detail="sessão não encontrada")
        return [e.model_dump(mode="json") for e in store.get_events(session_id)]

    @app.get("/api/sessions/{session_id}/timeline")
    async def get_session_timeline(session_id: str):
        if store.get_session(session_id) is None:
            raise HTTPException(status_code=404, detail="sessão não encontrada")
        return [t.model_dump(mode="json", by_alias=True) for t in store.get_timeline(session_id)]

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
        connected_websockets.add(websocket)
        try:
            while True:
                try:
                    message = await websocket.receive_json()
                except WebSocketDisconnect:
                    raise
                except Exception:
                    # mensagem que nao e JSON valido: ignora, nao derruba a conexao
                    continue

                if not isinstance(message, dict):
                    continue

                msg_type = message.get("type")
                if msg_type == "demo_start":
                    await demo_player.start()
                elif msg_type == "demo_stop":
                    await demo_player.stop()
        except WebSocketDisconnect:
            pass
        finally:
            connected_websockets.discard(websocket)

    if static_dir is not None and static_dir.is_dir():
        # Montado por último: rotas de API sempre têm prioridade sobre
        # arquivo estático de mesmo caminho.
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")

    return app
