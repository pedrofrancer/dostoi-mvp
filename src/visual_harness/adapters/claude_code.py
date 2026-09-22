"""Adapter do Claude Code (TechSpecs Seção 13-15): traduz o payload cru
de um hook do Claude Code pro modelo de evento comum. A heurística de
erro em `_looks_like_error` vem do `dostoi/state.py` original (a
primeira versão, texto puro, MVP anterior a este pacote); reaproveitada,
não reescrita do zero.
"""
from visual_harness.adapters.base import AdapterCapabilities, AdapterHealth
from visual_harness.events.models import Event
from visual_harness.events.types import EventType

# O que este adapter de fato observa (Seção 14): sem acesso a
# resultado de teste estruturado (só sucesso/falha genérico de
# comando) e sem acesso a plano/raciocínio interno (Seção 25: nunca
# assumir chain-of-thought). Hooks entregam JSON estruturado, não
# texto raspado de tela.
CLAUDE_CODE_CAPABILITIES = AdapterCapabilities(
    tool_events=True,
    file_events=True,
    command_events=True,
    test_events=False,
    user_messages=True,
    planning_events=False,
    structured_output=True,
)

_READ_TOOLS = {"Read"}
_SEARCH_TOOLS = {"Glob", "Grep"}
_EDIT_TOOLS = {"Edit", "Write"}
_RUN_TOOLS = {"Bash", "PowerShell"}
_WAIT_TOOLS = {"AskUserQuestion", "ExitPlanMode"}


def _looks_like_error(tool_response: dict | None) -> bool:
    if not isinstance(tool_response, dict):
        return False
    if tool_response.get("is_error") is True:
        return True
    if tool_response.get("error"):
        return True
    return False


def translate_hook_event(payload: dict) -> Event | None:
    """Traduz um payload de hook do Claude Code pro schema de evento
    comum (Seção 7). Devolve None quando o hook não mapeia pra nenhum
    EventType canônico — melhor omitir do que forçar um tipo errado.
    """
    session_id = payload.get("session_id")
    if not session_id:
        return None

    hook = payload.get("hook_event_name")
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response")

    event_type: EventType | None = None
    event_payload: dict = {}

    if hook == "SessionStart":
        event_type = EventType.AGENT_STARTED
    elif hook == "Stop":
        event_type = EventType.AGENT_STOPPED
    elif hook == "UserPromptSubmit":
        event_type = EventType.USER_MESSAGE
        prompt = payload.get("prompt")
        if prompt:
            event_payload["text"] = prompt

    elif hook == "PreToolUse" and tool_name in _WAIT_TOOLS:
        event_type = EventType.AGENT_WAITING

    elif hook == "PreToolUse" and tool_name in _RUN_TOOLS:
        event_type = EventType.COMMAND_STARTED
        event_payload["command"] = tool_input.get("command", "")

    elif hook == "PostToolUse" and tool_name in _RUN_TOOLS:
        event_type = (
            EventType.COMMAND_FAILED if _looks_like_error(tool_response) else EventType.COMMAND_FINISHED
        )
        event_payload["command"] = tool_input.get("command", "")

    elif hook == "PostToolUse" and tool_name in _READ_TOOLS:
        event_type = EventType.FILE_READ
        event_payload["path"] = tool_input.get("file_path", "")

    elif hook == "PostToolUse" and tool_name in _SEARCH_TOOLS:
        event_type = EventType.FILE_SEARCHED
        event_payload["path"] = tool_input.get("pattern") or tool_input.get("path", "")

    elif hook == "PostToolUse" and tool_name in _EDIT_TOOLS:
        event_type = EventType.FILE_MODIFIED
        event_payload["path"] = tool_input.get("file_path", "")

    # Agent/Task (delegação) e ferramentas desconhecidas: nenhum
    # EventType canônico cobre isso hoje. Melhor não emitir do que
    # forçar um tipo que não corresponde ao que de fato aconteceu.

    if event_type is None:
        return None

    return Event(
        session_id=session_id,
        source="claude-code",
        type=event_type,
        payload=event_payload,
    )


class ClaudeCodeAdapter:
    """Satisfaz o protocolo AgentAdapter (Seção 13). start/stop/health
    são bookkeeping leve: a ingestão de verdade acontece fora do
    processo do backend, no script de hook (`hooks/claude_code_hook.py`),
    que chama `translate_hook_event` e faz POST em /api/events. O
    Claude Code invoca um processo novo por hook; não existe conexão
    persistente pra este adapter monitorar.
    """

    name = "claude-code"

    def __init__(self) -> None:
        self._started = False

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._started = False

    async def health(self) -> AdapterHealth:
        if self._started:
            return AdapterHealth(healthy=True, detail="ativo")
        return AdapterHealth(healthy=False, detail="não iniciado")

    def capabilities(self) -> AdapterCapabilities:
        return CLAUDE_CODE_CAPABILITIES
