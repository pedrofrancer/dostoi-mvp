#!/usr/bin/env python3
"""Claude Code hook entrypoint: reads one hook payload from stdin,
normalizes it, and appends one JSON line to the Dostói event log.

Wired via .claude/settings.json hooks (PreToolUse, PostToolUse, Stop,
SessionStart, Notification). Never fails loudly: a hook that errors out
would interrupt Claude Code's own turn, so any problem here is swallowed
and the script exits 0.
"""
import json
import os
import sys
import time

DEFAULT_EVENTS_PATH = os.path.join(
    os.path.expanduser("~"), ".dostoi", "events.jsonl"
)


def events_path():
    return os.environ.get("DOSTOI_EVENTS_PATH", DEFAULT_EVENTS_PATH)


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    record = {
        "ts": time.time(),
        "hook": payload.get("hook_event_name", "unknown"),
        "session_id": payload.get("session_id"),
        "tool_name": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "tool_response": payload.get("tool_response"),
        "cwd": payload.get("cwd"),
    }

    path = events_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
