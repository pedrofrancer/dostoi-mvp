"""Cliente WebSocket do overlay de terminal (TechSpecs Seção 32, 58): o
mesmo `/ws` que o frontend browser consumia, o backend não muda nada
(Seção 32 é explícita sobre isso). Reconexão com o mesmo backoff do
cliente browser (1s, 2s, 4s, 8s, 16s, teto 30s).
"""
import asyncio
import json

import websockets

from visual_harness.terminal.renderer import TerminalOverlay

BACKOFF_STEPS_SECONDS = (1, 2, 4, 8, 16, 30)
LAYER2_POPUP_SECONDS = 6.0


async def _handle_layer2(overlay: TerminalOverlay, payload: dict) -> None:
    overlay.render_layer2(payload)
    await asyncio.sleep(LAYER2_POPUP_SECONDS)
    overlay.clear_layer2()


def dispatch(overlay: TerminalOverlay, message: dict) -> asyncio.Task | None:
    """Devolve a task do popup de Camada 2 quando dispara uma, pra
    quem chama poder cancelar se outro popup chegar antes de sumir."""
    msg_type = message.get("type")
    payload = message.get("payload") or {}
    if msg_type == "state_update":
        overlay.render_state(payload)
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
                    async for raw in websocket:
                        try:
                            message = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(message, dict):
                            continue

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
