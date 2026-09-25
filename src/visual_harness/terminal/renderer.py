"""Overlay de terminal, modo compacto (TechSpecs Seção 18-19, 57-59).

A região reservada (últimas `region_height` linhas da janela) fica
imune ao scroll do agente via DECSTBM (Seção 4/5: o overlay desenha no
MESMO tty do agente, processo separado, sem multiplexador). Em volta
de cada desenho: salva o cursor de verdade (onde o agente está agora),
escreve na região reservada, restaura o cursor pro agente continuar
exatamente de onde parou. Redesenha só quando o conteúdo muda, pra
evitar tempestade de animação (Seção 57).

Limite conhecido: resize de terminal em pleno `vh watch` não é tratado
(Windows não tem SIGWINCH); reinicie o comando se redimensionar.
"""
import shutil
import sys

from visual_harness.terminal import ansi
from visual_harness.terminal.glyphs import glyph_for

REGION_HEIGHT = 6
BOX_INNER_WIDTH = 15
POPUP_INNER_WIDTH = 40


def _center(text: str, width: int) -> str:
    text = text[:width]
    pad = width - len(text)
    left = pad // 2
    return " " * left + text + " " * (pad - left)


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _state_box(state: str, expression: str) -> list[str]:
    glyph = glyph_for(expression)
    label = state.capitalize()
    top = "┌" + "─" * (BOX_INNER_WIDTH + 2) + "┐"
    bottom = "└" + "─" * (BOX_INNER_WIDTH + 2) + "┘"
    return [
        top,
        "│ " + _center(glyph, BOX_INNER_WIDTH) + " │",
        "│ " + _center(label, BOX_INNER_WIDTH) + " │",
        bottom,
    ]


def _layer2_box(message: str) -> list[str]:
    top = "╭" + "─" * (POPUP_INNER_WIDTH + 2) + "╮"
    bottom = "╰" + "─" * (POPUP_INNER_WIDTH + 2) + "╯"
    body = [
        "│ " + line.ljust(POPUP_INNER_WIDTH) + " │"
        for line in _wrap(message, POPUP_INNER_WIDTH)[: REGION_HEIGHT - 2]
    ]
    return [top, *body, bottom]


class TerminalOverlay:
    """Modo compacto (issue Step 16): avatar + rótulo de estado, popup
    transitório de Camada 2. Painel de contexto e timeline completos
    ficam pra depois, como o checklist pede."""

    def __init__(self, stream=None, region_height: int = REGION_HEIGHT, rows: int | None = None):
        self._stream = stream if stream is not None else sys.stdout
        self._region_height = region_height
        self._rows = rows or 24
        self._fixed_rows = rows is not None  # testabilidade: pula a consulta ao SO
        self._started = False
        self._last_key = None
        self._last_state_payload: dict | None = None

    def start(self) -> None:
        if not self._fixed_rows:
            _, self._rows = shutil.get_terminal_size(fallback=(80, 24))
        # abre espaco empurrando o conteudo existente pra cima antes de
        # reservar a regiao, senao o que ja estava nas ultimas linhas
        # fica preso atras do overlay.
        self._write("\n" * self._region_height)
        self._write(ansi.set_scroll_region(1, self._rows - self._region_height))
        self._write(ansi.HIDE_CURSOR)
        self._started = True
        self._last_key = None

    def stop(self) -> None:
        if not self._started:
            return
        self._write(ansi.reset_scroll_region())
        self._write(ansi.SHOW_CURSOR)
        self._started = False

    def _write(self, text: str) -> None:
        self._stream.write(text)
        self._stream.flush()

    def _draw(self, lines: list[str], key) -> None:
        if key == self._last_key:
            return
        self._last_key = key
        if not self._started:
            return
        start_row = self._rows - self._region_height + 1
        self._write(ansi.SAVE_CURSOR)
        for offset in range(self._region_height):
            row_text = lines[offset] if offset < len(lines) else ""
            self._write(ansi.move_to(start_row + offset, 1) + ansi.CLEAR_LINE + row_text)
        self._write(ansi.RESTORE_CURSOR)

    def render_state(self, payload: dict) -> None:
        self._last_state_payload = payload
        humanization = payload.get("humanization") or {}
        expression = humanization.get("expression", "neutral")
        state = payload.get("state", "unknown")
        self._draw(_state_box(state, expression), key=("state", state, expression))

    def render_layer2(self, payload: dict) -> None:
        message = payload.get("message", "")
        self._draw(_layer2_box(message), key=("layer2", message))

    def clear_layer2(self) -> None:
        """Popup de Camada 2 some sozinho (Seção 18): volta pra caixa
        de estado que já estava sendo mostrada, ou fica em branco se
        nenhum state_update chegou ainda."""
        self._last_key = None  # o popup pode ter sido a ultima chave desenhada
        if self._last_state_payload is not None:
            self.render_state(self._last_state_payload)
        else:
            self._draw([], key=("empty",))

    def render_reconnecting(self, delay: float) -> None:
        lines = ["Connection lost", f"Retrying in {delay:.0f}s..."]
        self._draw(lines, key=("reconnecting", delay))

    def render_connected(self) -> None:
        self._last_key = None  # forca redesenho no proximo state_update
