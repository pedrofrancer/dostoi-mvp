# Adapters

## Contrato (`visual_harness.adapters.base`)

```python
class AgentAdapter(Protocol):
    name: str
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health(self) -> AdapterHealth: ...
    def capabilities(self) -> AdapterCapabilities: ...
```

`AdapterCapabilities` declara o que o adapter *de fato* observa
(`tool_events`, `file_events`, `command_events`, `test_events`,
`user_messages`, `planning_events`, `structured_output`) — o núcleo
nunca assume sinal que o adapter não declarou ter.

## Claude Code (`visual_harness.adapters.claude_code`)

Primeiro adapter real. Duas peças:

- `translate_hook_event(payload: dict) -> Event | None`: função pura,
  traduz um payload de hook do Claude Code pro schema de evento comum.
  Devolve `None` quando o hook não mapeia pra nenhum `EventType`
  canônico (ex.: delegação via `Agent`/`Task`, sem tipo correspondente
  hoje) — melhor omitir do que forçar um tipo errado.
- `ClaudeCodeAdapter`: satisfaz o protocolo. `start`/`stop`/`health` são
  bookkeeping leve, não uma conexão persistente: o Claude Code invoca
  um processo novo por hook, não existe conexão pra manter viva.

### O que este adapter observa

| Capacidade | Valor | Por quê |
|---|---|---|
| `tool_events` | ✓ | todo hook de ferramenta vira evento |
| `file_events` | ✓ | Read/Glob/Grep/Edit/Write mapeados |
| `command_events` | ✓ | Bash/PowerShell, início e fim |
| `test_events` | ✗ | só sabemos se o comando falhou, não se era teste |
| `user_messages` | ✓ | `UserPromptSubmit` |
| `planning_events` | ✗ | sem acesso a plano/raciocínio interno (Seção 25) |
| `structured_output` | ✓ | hook entrega JSON, não texto raspado |

### Mapa de tradução

| Hook | Tool | EventType |
|---|---|---|
| `SessionStart` | — | `agent_started` |
| `Stop` | — | `agent_stopped` |
| `UserPromptSubmit` | — | `user_message` (payload.text se `prompt` vier no hook) |
| `PreToolUse` | `Bash`/`PowerShell` | `command_started` |
| `PostToolUse` | `Bash`/`PowerShell` | `command_finished` ou `command_failed` |
| `PostToolUse` | `Read` | `file_read` |
| `PostToolUse` | `Glob`/`Grep` | `file_searched` |
| `PostToolUse` | `Edit`/`Write` | `file_modified` |
| `PreToolUse` | `AskUserQuestion`/`ExitPlanMode` | `agent_waiting` |
| qualquer outro | — | nada emitido (`None`) |

## Plugando no Claude Code

Em `.claude/settings.json` (ou `settings.local.json`) do projeto que o
agente vai codar:

```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/claude_code_hook.py" }] }],
    "PreToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/claude_code_hook.py" }] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/claude_code_hook.py" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/claude_code_hook.py" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/claude_code_hook.py" }] }]
  }
}
```

O script lê o payload do hook, traduz, e faz `POST` em
`http://127.0.0.1:8765/api/events` (configurável via `VH_HOST`/`VH_PORT`).
Nunca falha alto: qualquer problema é engolido e o script sempre sai
com código 0, porque um hook quebrado pararia o próprio turno do Claude
Code (Seção 41-42).

Sucessor do `hooks/emit_event.py` do MVP em texto original (`dostoi/`):
aquele só gravava JSONL; este traduz pro schema de evento comum e
envia pro backend de verdade. O `dostoi/` continua intacto como estava,
não foi tocado.
