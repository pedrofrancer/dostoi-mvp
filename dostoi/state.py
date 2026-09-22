"""Camada 1: classifica cada evento bruto (hook do Claude Code) num estado
operacional do avatar. Determinístico, sem chamada de rede: o objetivo é
que o estado reflita o que o agente está fazendo agora, não uma opinião
sobre isso (isso é trabalho da Camada 2).
"""

READ_TOOLS = {"Read", "Glob", "Grep"}
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}
RUN_TOOLS = {"Bash", "PowerShell"}
DELEGATE_TOOLS = {"Agent", "Task"}
WAIT_TOOLS = {"AskUserQuestion", "ExitPlanMode"}

STATE_IDLE = "IDLE"
STATE_READING = "READING"
STATE_EDITING = "EDITING"
STATE_RUNNING = "RUNNING"
STATE_DELEGATING = "DELEGATING"
STATE_WAITING = "WAITING"
STATE_WORKING = "WORKING"
STATE_ERROR = "ERROR"


def _looks_like_error(tool_response):
    """Heurística: Claude Code não expõe um campo de erro uniforme entre
    ferramentas, então procuramos os sinais mais comuns antes de decidir
    que algo falhou."""
    if not isinstance(tool_response, dict):
        return False
    if tool_response.get("is_error") is True:
        return True
    if tool_response.get("error"):
        return True
    return False


def classify(event):
    """Recebe um evento normalizado (ver hooks/emit_event.py) e devolve
    (estado, detalhe) para a Camada 1."""
    hook = event.get("hook")
    tool_name = event.get("tool_name")
    tool_input = event.get("tool_input") or {}

    if hook == "SessionStart":
        return STATE_IDLE, "sessão iniciada"
    if hook == "Stop":
        return STATE_IDLE, "turno encerrado"
    if hook == "UserPromptSubmit":
        return STATE_WORKING, "novo pedido recebido"

    if hook == "PostToolUse" and _looks_like_error(event.get("tool_response")):
        return STATE_ERROR, f"{tool_name} falhou"

    if tool_name in READ_TOOLS:
        alvo = tool_input.get("file_path") or tool_input.get("pattern") or ""
        return STATE_READING, alvo
    if tool_name in EDIT_TOOLS:
        alvo = tool_input.get("file_path") or ""
        return STATE_EDITING, alvo
    if tool_name in RUN_TOOLS:
        alvo = tool_input.get("command") or ""
        return STATE_RUNNING, alvo
    if tool_name in DELEGATE_TOOLS:
        return STATE_DELEGATING, tool_input.get("description") or ""
    if tool_name in WAIT_TOOLS:
        return STATE_WAITING, ""

    if tool_name:
        return STATE_WORKING, tool_name

    return STATE_IDLE, ""
