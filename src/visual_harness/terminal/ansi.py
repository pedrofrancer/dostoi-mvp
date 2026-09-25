"""Sequências VT/ANSI cruas (TechSpecs Seção 4): a abstração de uma
biblioteca como `rich` atrapalharia o controle fino de cursor que o
overlay precisa (redesenhar só a própria região, Seção 57), então o
renderer escreve a sequência direto.
"""

ESC = "\x1b"

SAVE_CURSOR = f"{ESC}7"  # DECSC, mais suportado que o \x1b[s do ANSI.SYS
RESTORE_CURSOR = f"{ESC}8"  # DECRC
HIDE_CURSOR = f"{ESC}[?25l"
SHOW_CURSOR = f"{ESC}[?25h"
CLEAR_LINE = f"{ESC}[2K"
RESET = f"{ESC}[0m"

_FG_CODES = {
    "default": 39,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "cyan": 36,
    "magenta": 35,
}


def move_to(row: int, col: int) -> str:
    return f"{ESC}[{row};{col}H"


def set_scroll_region(top: int, bottom: int) -> str:
    """DECSTBM: trava as linhas fora de [top, bottom] contra o próprio
    scroll do terminal. É o que deixa a região do overlay parada
    enquanto a saída do agente, num PROCESSO separado, rola por cima
    (mesmo truque das barras de status do tmux/vim: o terminal aplica
    isso pra qualquer processo que escrever nele, não só pra quem
    setou)."""
    return f"{ESC}[{top};{bottom}r"


def reset_scroll_region() -> str:
    return f"{ESC}[r"


def cursor_down(n: int) -> str:
    return f"{ESC}[{n}B" if n else ""


def cursor_up(n: int) -> str:
    return f"{ESC}[{n}A" if n else ""


def fg(color: str, text: str) -> str:
    code = _FG_CODES.get(color, _FG_CODES["default"])
    return f"{ESC}[{code}m{text}{RESET}"
