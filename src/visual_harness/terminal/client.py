"""Cliente WebSocket do overlay de terminal (TechSpecs Seção 32, 58): o
mesmo `/ws` que o frontend browser consumia, o backend não muda nada
(Seção 32 é explícita sobre isso). Reconexão com o mesmo backoff do
cliente browser (1s, 2s, 4s, 8s, 16s, teto 30s). Hidrata contexto e
linha do tempo por REST (Step 18) assim que descobre a sessão, uma vez
por conexão, nunca em intervalo (Seção 76: sem polling).
"""
import asyncio
import json

import httpx
import websockets

from visual_harness.terminal.renderer import TerminalOverlay

BACKOFF_STEPS_SECONDS = (1, 2, 4, 8, 16, 30)
LAYER2_POPUP_SECONDS = 6.0
HYDRATE_TIMEOUT_SECONDS = 3.0


async def _handle_layer2(overlay: TerminalOverlay, payload: dict) -> None:
    overlay.render_layer2(payload)
    await asyncio.sleep(LAYER2_POPUP_SECONDS)
    overlay.clear_layer2()


async def discover_active_session(host: str, port: int) -> str | None:
    """Sessão pra hidratar sem esperar mensagem ao vivo nenhuma (Step
    18): só quando existe EXATAMENTE uma sessão, senão a ambiguidade de
    qual delas mostrar não é deste cliente resolver, fica pro
    reativo (a primeira que aparecer ao vivo)."""
    base = f"http://{host}:{port}"
    try:
        async with httpx.AsyncClient(timeout=HYDRATE_TIMEOUT_SECONDS) as http:
            response = await http.get(f"{base}/api/sessions")
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    sessions = response.json()
    if len(sessions) != 1:
        return None
    return sessions[0].get("id")


async def hydrate(host: str, port: int, session_id: str, overlay: TerminalOverlay) -> None:
    """Busca o contexto e a linha do tempo que já existiam antes desta
    conexão (Step 18); falha aqui nunca derruba `vh watch`, o overlay
    só fica vazio até a próxima mensagem ao vivo."""
    base = f"http://{host}:{port}"
    async with httpx.AsyncClient(timeout=HYDRATE_TIMEOUT_SECONDS) as http:
        try:
            session_response = await http.get(f"{base}/api/sessions/{session_id}")
            if session_response.status_code == 200:
                context = session_response.json().get("context")
                if context is not None:
                    overlay.render_context({"session_id": session_id, "context": context})
        except httpx.HTTPError:
            pass

        try:
            timeline_response = await http.get(f"{base}/api/sessions/{session_id}/timeline")
            if timeline_response.status_code == 200:
                for transition in timeline_response.json():
                    overlay.render_timeline_entry(
                        {"session_id": session_id, "transition": transition}
                    )
        except httpx.HTTPError:
            pass


def dispatch(overlay: TerminalOverlay, message: dict) -> asyncio.Task | None:
    """Devolve a task do popup de Camada 2 quando dispara uma, pra
    quem chama poder cancelar se outro popup chegar antes de sumir."""
    msg_type = message.get("type")
    payload = message.get("payload") or {}
    if msg_type == "state_update":
        overlay.render_state(payload)
    elif msg_type == "session_update":
        overlay.render_context(payload)
    elif msg_type == "timeline_update":
        overlay.render_timeline_entry(payload)
    elif msg_type == "layer2_update":
        return asyncio.ensure_future(_handle_layer2(overlay, payload))
    return None


async def run(host: str, port: int, overlay: TerminalOverlay) -> None:
    """Roda pra sempre (até ser cancelada de fora): conecta, escuta,
    reconecta com backoff quando cai."""
    uri = f"ws://{host}:{port}/ws"
    attempt = 0
    popup_task: asyncio.Task | None = None
    try:
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    attempt = 0
                    overlay.render_connected()
                    hydrated_session_id: str | None = None

                    active_session_id = await discover_active_session(host, port)
                    if active_session_id is not None:
                        await hydrate(host, port, active_session_id, overlay)
                        hydrated_session_id = active_session_id

                    async for raw in websocket:
                        try:
                            message = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(message, dict):
                            continue

                        session_id = (message.get("payload") or {}).get("session_id")
                        if session_id and session_id != hydrated_session_id:
                            await hydrate(host, port, session_id, overlay)
                            hydrated_session_id = session_id

                        if message.get("type") == "layer2_update" and popup_task is not None:
                            popup_task.cancel()
                        task = dispatch(overlay, message)
                        if task is not None:
                            popup_task = task
            except (OSError, websockets.exceptions.WebSocketException):
                delay = BACKOFF_STEPS_SECONDS[min(attempt, len(BACKOFF_STEPS_SECONDS) - 1)]
                overlay.render_reconnecting(delay)
                attempt += 1
                await asyncio.sleep(delay)
    finally:
        if popup_task is not None:
            popup_task.cancel()
