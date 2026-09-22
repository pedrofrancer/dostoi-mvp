# Eventos

## Modelo (`visual_harness.events.models.Event`)

Todo evento tem: `id` (UUIDv7, cronologicamente ordenável), `session_id`,
`timestamp`, `source`, `type` (um dos valores de
`visual_harness.events.types.EventType`), `version` (1), `payload` e
`sequence` (atribuído pelo `EventBus`, não pelo chamador).

Alguns tipos exigem campo obrigatório no `payload` — os únicos com
schema definido no TechSpecs (Seção 10, exemplos concretos):

| Tipo | Campo obrigatório |
|---|---|
| `file_read`, `file_created`, `file_modified`, `file_deleted`, `file_searched` | `path` |
| `command_started`, `command_finished`, `command_failed` | `command` |
| `test_failed` | `test` |
| `test_suite_completed` | `passed`, `failed` |

Os demais tipos aceitam qualquer `payload` (dict), porque o TechSpecs
(Seção 50) ainda deixa esse schema em aberto.

## Emitindo eventos pelo `vh`

```bash
vh event --type file_read --path src/main.py --session s1
vh event --type command_started --command "npm test"
vh event --json '{"session_id": "s1", "source": "cli", "type": "test_failed", "payload": {"test": "login"}}'
```

### Quoting no PowerShell (TechSpecs Seção 37)

Testado de verdade, não por suposição: ao repassar um argumento com
aspas duplas pra um executável nativo (como `vh`), o PowerShell come as
aspas internas antes delas chegarem no processo, mesmo dentro de uma
string de aspas duplas com `` `" `` escapado. O JSON chega sem aspas
nenhuma e `json.loads` quebra.

O que funciona: aspas simples por fora (não interpoladas pelo
PowerShell) com `\"` literal por dentro — o parser de linha de comando
do Windows é quem entende esse `\"`, não o PowerShell:

```powershell
vh event --json '{\"type\": \"test_failed\", \"session_id\": \"s1\", \"source\": \"cli\", \"payload\": {\"test\": \"login\"}}'
```

Mais simples ainda: use as flags dedicadas (`--path`, `--command`) em
vez de `--json` sempre que o payload for só isso — evita o problema de
quoting por completo.
