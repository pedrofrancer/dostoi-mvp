#!/usr/bin/env python3
"""Entrypoint de hook do Claude Code pro Visual Harness (Step 12).
Sucessor do `hooks/emit_event.py` do MVP em texto original (dostoi/):
aquele só logava JSONL, este traduz pro schema de evento comum
(`visual_harness.adapters.claude_code.translate_hook_event`) e envia
pro backend de verdade via POST /api/events.

Nunca falha alto: um hook que der erro interromperia o próprio turno
do Claude Code (Seção 41-42, reliability). Qualquer problema aqui é
engolido, e o script sempre sai com código 0.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

DEFAULT_HOST = os.environ.get("VH_HOST", "127.0.0.1")
DEFAULT_PORT = os.environ.get("VH_PORT", "8765")


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        sys.exit(0)

    try:
        from visual_harness.adapters.claude_code import translate_hook_event

        event = translate_hook_event(payload)
        if event is None:
            sys.exit(0)

        import httpx

        httpx.post(
            f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api/events",
            json=event.model_dump(mode="json"),
            timeout=1.0,
        )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
