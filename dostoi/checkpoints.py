"""Detecta os pontos-chave em que a Camada 2 deve se manifestar. Um
checkpoint não é um estado (isso é Camada 1); é um evento que merece um
julgamento sobre o que acabou de acontecer.

MVP com dois gatilhos, deliberadamente poucos: falha de comando e
retrabalho no mesmo arquivo. Mais gatilhos só depois que estes dois
provarem, em texto, que fazem sentido.
"""
import time

REWORK_WINDOW_SECONDS = 300
REWORK_LOOKBACK = 8


def _bash_failed(event):
    if event.get("tool_name") not in ("Bash", "PowerShell"):
        return False
    resp = event.get("tool_response")
    if not isinstance(resp, dict):
        return False
    if resp.get("is_error") is True:
        return True
    code = resp.get("exit_code") if "exit_code" in resp else resp.get("returncode")
    return isinstance(code, int) and code != 0


def detect(event, history):
    """event: registro normalizado atual (já deve ser PostToolUse).
    history: lista dos últimos eventos PostToolUse, mais recente por último
    (não inclui o `event` atual).

    Devolve uma lista de (tipo_checkpoint, contexto) — geralmente 0 ou 1
    item, mas nada impede mais de um no mesmo evento.
    """
    achados = []

    if _bash_failed(event):
        cmd = (event.get("tool_input") or {}).get("command", "")
        achados.append(("test_failure", {"command": cmd, "event": event}))

    tool_name = event.get("tool_name")
    if tool_name in ("Edit", "Write"):
        alvo = (event.get("tool_input") or {}).get("file_path")
        if alvo:
            agora = event.get("ts", time.time())
            janela = history[-REWORK_LOOKBACK:]
            for anterior in reversed(janela):
                if anterior.get("tool_name") not in ("Edit", "Write"):
                    continue
                outro_alvo = (anterior.get("tool_input") or {}).get("file_path")
                if outro_alvo != alvo:
                    continue
                delta = agora - anterior.get("ts", agora)
                if 0 <= delta <= REWORK_WINDOW_SECONDS:
                    achados.append(
                        ("rework", {"file_path": alvo, "seconds_since": delta})
                    )
                break

    return achados
