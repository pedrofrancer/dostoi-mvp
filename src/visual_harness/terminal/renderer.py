"""Overlay de terminal (TechSpecs Seção 18-19, 57-59): compacto, cheio
e minimal.

A região reservada (últimas `region_height` linhas da janela) fica
imune ao scroll do agente via DECSTBM (Seção 4/5: o overlay desenha no
MESMO tty do agente, processo separado, sem multiplexador). Em volta
de cada desenho: salva o cursor de verdade (onde o agente está agora),
escreve na região reservada, restaura o cursor pro agente continuar
exatamente de onde parou.

Limite conhecido: resize de terminal em pleno `vh watch` não é tratado
(Windows não tem SIGWINCH); reinicie o comando se redimensionar. Modo
cheio não hidrata contexto/linha do tempo de antes da conexão (Step
17): começa vazio e preenche ao vivo.
"""
import re
import shutil
import sys

from visual_harness.terminal import ansi
from visual_harness.terminal.glyphs import glyph_for

# Seção 40 (Security Requirements) não cobria isso porque não existia
# terminal ainda: task/agent (payload de evento) e a mensagem de
# Camada 2 chegam de fora do processo sem garantia de conteúdo. Sem
# isso, um payload malicioso escreveria sequência de escape ANSI de
# verdade no terminal de quem estiver rodando `vh watch` (troca de
# título, reposicionamento de cursor, o que o emulador aceitar).
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _sanitize(text: str) -> str:
    return _CONTROL_CHARS.sub("", text)

MODE_COMPACT = "compact"
MODE_FULL = "full"
MODE_MINIMAL = "minimal"

TIMELINE_MAX_ENTRIES = 5

BOX_INNER_WIDTH = 15
POPUP_INNER_WIDTH = 40
FULL_INNER_WIDTH = 30

REGION_HEIGHT_BY_MODE = {
    MODE_MINIMAL: 1,
    MODE_COMPACT: 6,
    MODE_FULL: 4 + 1 + 6 + (2 + TIMELINE_MAX_ENTRIES),
}


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
    label = _sanitize(state).capitalize()
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
        for line in _wrap(_sanitize(message), POPUP_INNER_WIDTH)[:TIMELINE_MAX_ENTRIES]
    ]
    return [top, *body, bottom]


def _titled_border(title: str, inner_width: int, corners: tuple[str, str]) -> str:
    header = f"{corners[0]} {title} "
    total = inner_width + 4
    pad = max(total - len(header) - 1, 0)
    return header + "─" * pad + corners[1]


def _row(label: str, value: str, inner_width: int) -> str:
    text = f"{label.ljust(9)}{value}"[:inner_width].ljust(inner_width)
    return "│ " + text + " │"


def _context_lines(context: dict, inner_width: int) -> list[str]:
    task = _sanitize(str(context.get("task") or "-"))
    agent = _sanitize(str(context.get("agent") or "-"))
    files = len(context.get("modified_files") or [])
    passed = context.get("tests_passed", 0)
    failed = context.get("tests_failed", 0)
    errors = len(context.get("recent_errors") or [])
    return [
        _titled_border("CONTEXTO", inner_width, ("┌", "┐")),
        _row("Tarefa", str(task), inner_width),
        _row("Agente", str(agent), inner_width),
        _row("Arquivos", f"{files} modificados", inner_width),
        _row("Testes", f"{passed} / {failed}", inner_width),
        _row("Erros", str(errors), inner_width),
    ]


def _timeline_lines(entries: list[str], inner_width: int) -> list[str]:
    lines = [_titled_border("LINHA DO TEMPO", inner_width, ("├", "┤"))]
    for index, label in enumerate(entries):
        marker = "→" if index == len(entries) - 1 else "✓"
        text = f"{marker} {_sanitize(label)}"[:inner_width].ljust(inner_width)
        lines.append("│ " + text + " │")
    lines.append("└" + "─" * (inner_width + 2) + "┘")
    return lines


class TerminalOverlay:
    """Três modos (Seção 19): `compact` (padrão, avatar + estado, Step
    16), `full` (avatar + painel de contexto + linha do tempo, Step
    17), `minimal` (só o glifo). Trava na primeira sessão que aparece,
    ignora mensagem de outra sessão daí em diante."""

    def __init__(self, stream=None, mode: str = MODE_COMPACT, rows: int | None = None):
        self._stream = stream if stream is not None else sys.stdout
        self._mode = mode
        self._region_height = REGION_HEIGHT_BY_MODE[mode]
        self._rows = rows or 24
        self._fixed_rows = rows is not None  # testabilidade: pula a consulta ao SO
        self._started = False
        self._last_key = None
        self._draw_counter = 0
        self._session_id: str | None = None
        self._last_state_payload: dict | None = None
        self._last_context: dict = {}
        self._timeline_labels: list[str] = []

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

    def _accept(self, payload: dict) -> bool:
        """Primeira sessão que aparece vira a sessão travada (Step 17);
        mensagem de outra sessão é ignorada daí em diante."""
        session_id = payload.get("session_id")
        if self._session_id is None:
            self._session_id = session_id
        return session_id == self._session_id

    def _draw_full(self) -> None:
        humanization = (self._last_state_payload or {}).get("humanization") or {}
        expression = humanization.get("expression", "neutral")
        state = (self._last_state_payload or {}).get("state", "unknown")
        lines = [
            *_state_box(state, expression),
            "",
            *_context_lines(self._last_context, FULL_INNER_WIDTH),
            *_timeline_lines(self._timeline_labels, FULL_INNER_WIDTH),
        ]
        # cada chamada aqui já é reação a uma mensagem nova (Seção 57
        # fala de evitar redesenho SEM mudança de conteúdo, não este
        # caso); chave sempre nova em vez de tentar compor uma chave
        # estável a partir de três fontes diferentes de estado.
        self._draw_counter += 1
        self._draw(lines, key=("full", self._draw_counter))

    def render_state(self, payload: dict) -> None:
        if not self._accept(payload):
            return
        self._last_state_payload = payload
        humanization = payload.get("humanization") or {}
        expression = humanization.get("expression", "neutral")
        state = payload.get("state", "unknown")

        if self._mode == MODE_FULL:
            self._draw_full()
        elif self._mode == MODE_MINIMAL:
            self._draw([glyph_for(expression)], key=("minimal", state, expression))
        else:
            self._draw(_state_box(state, expression), key=("state", state, expression))

    def render_context(self, payload: dict) -> None:
        if not self._accept(payload):
            return
        self._last_context = payload.get("context") or {}
        if self._mode == MODE_FULL:
            self._draw_full()

    def render_timeline_entry(self, payload: dict) -> None:
        if not self._accept(payload):
            return
        transition = payload.get("transition") or {}
        label = str(transition.get("to") or "").capitalize()
        if label:
            self._timeline_labels.append(label)
            self._timeline_labels = self._timeline_labels[-TIMELINE_MAX_ENTRIES:]
        if self._mode == MODE_FULL:
            self._draw_full()

    def render_layer2(self, payload: dict) -> None:
        if not self._accept(payload):
            return
        message = payload.get("message", "")
        self._draw(_layer2_box(message), key=("layer2", message))

    def clear_layer2(self) -> None:
        """Popup de Camada 2 some sozinho (Seção 18): volta pro que já
        estava sendo mostrado, ou fica em branco se nada chegou ainda."""
        self._last_key = None  # o popup pode ter sido a ultima chave desenhada
        if self._mode == MODE_FULL:
            self._draw_full()
        elif self._last_state_payload is not None:
            self.render_state(self._last_state_payload)
        else:
            self._draw([], key=("empty",))

    def render_reconnecting(self, delay: float) -> None:
        lines = ["Connection lost", f"Retrying in {delay:.0f}s..."]
        self._draw(lines, key=("reconnecting", delay))

    def render_connected(self) -> None:
        self._last_key = None  # forca redesenho no proximo state_update
