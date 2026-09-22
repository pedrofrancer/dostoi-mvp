"""CLI do MVP: acompanha o log de eventos e imprime, em texto puro, o que
a Camada 1 e a Camada 2 enxergam. Sem avatar, sem desenho, de propósito
(ver README, seção "por que a ordem de construção importa").
"""
import argparse
import json
import sys
import time
from datetime import datetime

from dostoi import checkpoints, judge, state

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

POST_HISTORY_LIMIT = 50


def _fmt_ts(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


_FASE_POR_HOOK = {
    "PreToolUse": "inicio",
    "PostToolUse": "fim",
    "SessionStart": "inicio",
    "Stop": "fim",
    "UserPromptSubmit": "inicio",
}


def _print_layer1(event, estado, detalhe):
    ts = _fmt_ts(event.get("ts", time.time()))
    detalhe = f" {detalhe}" if detalhe else ""
    fase = _FASE_POR_HOOK.get(event.get("hook"), "?")
    print(f"[{ts}] camada1 {estado}{detalhe} ({fase})")


def _print_layer2(event, tipo, texto, origem):
    ts = _fmt_ts(event.get("ts", time.time()))
    print(f"[{ts}] camada2 ({tipo}, {origem}): {texto}")


def process_line(line, post_history):
    line = line.strip()
    if not line:
        return
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return

    estado, detalhe = state.classify(event)
    _print_layer1(event, estado, detalhe)

    if event.get("hook") == "PostToolUse":
        for tipo, contexto in checkpoints.detect(event, post_history):
            texto, origem = judge.comment(tipo, contexto)
            _print_layer2(event, tipo, texto, origem)
        post_history.append(event)
        del post_history[:-POST_HISTORY_LIMIT]


def tail(path, poll_seconds=0.5):
    post_history = []
    with open(path, "a", encoding="utf-8"):
        pass  # garante que o arquivo existe antes de abrir para leitura
    with open(path, "r", encoding="utf-8") as f:
        f.seek(0, 2)  # vai direto pro fim: só o que acontecer daqui pra frente
        while True:
            line = f.readline()
            if not line:
                time.sleep(poll_seconds)
                continue
            process_line(line, post_history)


def replay(path):
    post_history = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            process_line(line, post_history)


def main():
    parser = argparse.ArgumentParser(description="Dostói, Camadas 1 e 2 em texto.")
    parser.add_argument("--events", required=True, help="caminho do events.jsonl")
    parser.add_argument(
        "--once",
        action="store_true",
        help="processa o arquivo inteiro uma vez e sai, em vez de ficar seguindo",
    )
    args = parser.parse_args()

    if args.once:
        replay(args.events)
    else:
        tail(args.events)


if __name__ == "__main__":
    main()
