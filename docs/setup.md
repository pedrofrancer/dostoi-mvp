# Rodando o MVP (texto, sem avatar)

Este MVP não desenha nada ainda. Ele só prova que a Camada 1 (estado
operacional) e a Camada 2 (julgamento nos checkpoints) fazem sentido,
vendo tudo impresso como texto no terminal.

## 1. Wire os hooks no projeto que o agente vai codar

No projeto onde o Claude Code vai rodar (não neste repo do Dostói), edite
`.claude/settings.json` e adicione:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/emit_event.py" }] }
    ],
    "PreToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/emit_event.py" }] }
    ],
    "PostToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/emit_event.py" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "python C:/caminho/para/dostoi-mvp/hooks/emit_event.py" }] }
    ]
  }
}
```

Troque `C:/caminho/para/dostoi-mvp` pelo caminho real deste repo clonado.
Os eventos vão para `~/.dostoi/events.jsonl` por padrão (configurável via
`DOSTOI_EVENTS_PATH`, precisa ser a mesma variável nos hooks e no
watcher se você mudar o padrão).

## 2. Rode o watcher em outro terminal

```bash
cd dostoi-mvp
python -m dostoi.watch --events ~/.dostoi/events.jsonl
```

Ele fica parado esperando, imprimindo uma linha de Camada 1 a cada
ferramenta usada pelo agente, e uma linha de Camada 2 quando um
checkpoint (falha de comando, retrabalho no mesmo arquivo) acontece.

## 3. Julgamento real de Camada 2 (opcional)

Sem chave de API, os comentários da Camada 2 usam um template fixo por
tipo de checkpoint (funcional, mas óbvio demais pra valer o nome
"reflexivo"). Para o julgamento de verdade, gerado por modelo:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
```

O modelo usado é configurável via `DOSTOI_JUDGE_MODEL` (padrão:
`claude-haiku-4-5-20251001`, rápido e barato o bastante para rodar em
todo checkpoint sem virar gargalo).

## Testando sem hooks de verdade

`tests/` tem a suíte de unidade (Camada 1 e detecção de checkpoint, sem
rede). Para ver o watcher processando uma sessão inteira sem precisar
codar de verdade, gere um `events.jsonl` sintético (um JSON por linha, no
formato que `hooks/emit_event.py` produz) e rode:

```bash
python -m dostoi.watch --events caminho/para/events.jsonl --once
```

`--once` processa o arquivo inteiro e sai, em vez de ficar seguindo.
