# Dostói MVP

  <img width="576" alt="Dostói" src="https://i.pinimg.com/736x/cc/d4/35/ccd435211b4466ac3575571f2726166b.jpg" />

Passei anos formalizando processos que não conseguia ver por dentro,
ataques, provas, modelos de ameaça, e sempre sobrava a mesma frustração:
o raciocínio que importa acontece num lugar opaco, e o que chega até mim
é só o resíduo dele, um log, um terminal rolando texto. O Dostói nasce
dessa frustração específica, aplicada a um caso concreto: um agente de
IA codando, enquanto eu só enxergo a casca do que ele está pensando.

A resposta óbvia seria um avatar decorativo, reage a "rodando" com uma
carinha feliz, a "parado" com uma carinha de sono. Isso já existe, e não
resolve nada que me interesse. O que me interessa é uma frase que me
ocorreu enquanto pensava nisso:

> nós não somos nossos pensamentos, nós pensamos sobre eles

Um agente que só mostra que está trabalhando ainda é o agente sendo seus
próprios pensamentos, sem distância nenhuma deles. O que eu quero
construir é a distância: uma camada que observa o trabalho do agente e
forma um julgamento sobre ele. Não "estou trabalhando", e sim "estou
trabalhando, e essa abordagem me parece questionável".

## As duas camadas

### Camada 1, o que o agente está fazendo (operacional)

O corpo do avatar reagindo em tempo real: lendo código, executando algo,
esperando resultado, lidando com erro, mudando de direção. Contínuo,
sutil, uma linguagem corporal, postura, expressão, ritmo. É o agente
sendo seus pensamentos.

### Camada 2, o que o agente pensa sobre o próprio trabalho (metacognitiva)

Esta é a parte que me interessa de verdade. De tempos em tempos, não a
cada ação, mas em pontos de inflexão (depois de uma mudança de código
relevante, depois de um teste falhar, depois de uma reconsideração), o
avatar para e emite um comentário curto sobre o que acabou de acontecer.
Algo como "essa função já existe em outro lugar do código", ou "isso
resolve o sintoma, não a causa do erro anterior". É o agente pensando
sobre seus próprios pensamentos, a distância que dá ao projeto qualquer
qualidade reflexiva de verdade, em vez de só um indicador de status
bonito.

## Como isso se manifesta visualmente

A Camada 1 fica sempre ligada, de fundo, o avatar respirando, mudando de
postura, com microexpressões conforme o estado muda.

A Camada 2 aparece só nos checkpoints, como um balão de pensamento que
interrompe o fluxo contínuo, breve, pontual, dando a sensação de que o
avatar teve um insight sobre o trabalho, não apenas reagiu a ele.

## O sistema de "peles" (skins)

O avatar é desacoplado da lógica. A mesma consciência por trás, os
estados, os julgamentos, pode ser representada por avatares
completamente diferentes. A pele que está de pé hoje é um retrato 8-bit
que eu mesmo trouxe pro projeto: um único traçado de silhueta que
precisou de cirurgia, não de redesenho, pra virar expressivo (sobrancelha
e olho eram uma peça só, cortados numa aresta que já existia na própria
arte, e a boca era um recorte na borda do contorno que virou buraco
independente). A lógica de interpretação é uma coisa, a aparência é
outra; uma vez que o "cérebro" funcione, encaixar um personagem novo é
questão de desenhar em cima do mesmo contrato de partes, sem tocar no
raciocínio.

## Por que a ordem de construção importa

Já vi o suficiente de sistemas mal calibrados para saber onde mora o
risco real aqui: não é o avatar ficar bonito, é a parte de
"entendimento", Camada 1 e Camada 2, fazer sentido de verdade. Um avatar
que muda de estado de forma aleatória ou incoerente é pior que nenhum
avatar, é ruído com forma de sinal. Por isso o projeto seguiu, passo a
passo, a ordem que o próprio TechSpecs recomenda: primeiro provar que a
interpretação funciona em texto puro, só depois investir em desenho,
animação e variação de personagem.

## Onde isso chegou

Treze das quatorze etapas do roadmap fechadas; a última (testes de
integração, auditoria de segurança e performance, esta própria
documentação) em andamento no momento em que escrevo isto.

| Etapa | O que é | Estado |
|---|---|---|
| 1 | Repositório e empacotamento | fechada |
| 2 | Modelos de evento | fechada |
| 3 | Barramento de eventos | fechada |
| 4 | Motor de estado | fechada |
| 5 | Motor de humanização | fechada |
| 6 | Fonte de eventos de demo | fechada |
| 7 | API backend e WebSocket | fechada |
| 8 | Avatar SVG no frontend | fechada |
| 9 | Linha do tempo da sessão | fechada |
| 10 | Comando CLI genérico de evento | fechada |
| 11 | Persistência SQLite | fechada |
| 12 | Adapter do Claude Code | fechada |
| 13 | Privacidade e redaction | fechada |
| 14 | Testes e documentação | em andamento |

Histórico completo nas issues do repositório: as seis primeiras (#1 a
#6) foram fechadas quando o escopo pequeno do MVP em texto deu lugar ao
PRD/TechSpecs formal; as quatorze seguintes (#7 a #20) seguem a
Implementation Order do TechSpecs, uma issue por etapa.

## Arquitetura

Um evento nasce (hook do Claude Code, `vh event`, ou `POST /api/events`),
passa por um barramento assíncrono, e dali se ramifica: o motor de
estado decide o que está acontecendo, o motor de humanização traduz
isso em expressão e gesto, o store guarda a história (limitada em
memória, completa em SQLite), e o WebSocket manda tudo isso pro avatar
reagir ao vivo.

```
evento → EventBus → SessionStore → motor de estado → motor de humanização → WebSocket → avatar
                          │
                          ├→ SQLite (write-through, com redação opcional)
                          └→ detector de checkpoint → julgamento (LLM ou heurística) → WebSocket → popup de Camada 2
```

- `visual_harness/events/`: o contrato comum (`Event`, `EventType`,
  UUIDv7 pra ordenação cronológica) e o barramento.
- `visual_harness/state/`: os dezessete estados possíveis, a cascata de
  regras que decide qual deles vale, a arbitração de prioridade quando
  há sinal conflitante, a histerese que evita o avatar piscar demais.
- `visual_harness/humanization/`: o vocabulário visual (expressão,
  gesto, animação, mensagem curta) e a guarda que impede qualquer
  mensagem reivindicar experiência subjetiva ("reconsiderando
  abordagem", nunca "a IA está com medo").
- `visual_harness/context/`: o resumo de sessão, tarefa, arquivos
  tocados, testes, erros recentes, calculado a partir do histórico de
  eventos.
- `visual_harness/judgment/`: Camada 2, a metacognitiva (TechSpecs
  Seção 60.1). Detecta checkpoint (falha de comando ou teste,
  retrabalho no mesmo arquivo), redige o contexto antes de sair do
  processo, e pede o julgamento a um LLM por HTTP genérico compatível
  com OpenAI (qualquer provedor, incluindo os gratuitos: Groq,
  OpenRouter, Ollama local), com template fixo quando falta
  configuração ou rede.
- `visual_harness/server/`: a API REST, o WebSocket, e o store em
  memória que serve tudo isso rápido.
- `visual_harness/persistence/`: as quatro tabelas SQLite (sessions,
  events, state_transitions, context_snapshots) que guardam a história
  completa depois que a memória já esqueceu o começo.
- `visual_harness/privacy/`: redação de segredo antes de qualquer
  escrita em disco, três modos (strict, standard, debug).
- `visual_harness/adapters/`: o contrato que qualquer agente de IA
  precisa satisfazer pra alimentar o sistema, e a primeira
  implementação real, a tradução dos hooks do Claude Code.
- `visual_harness/demo/`: uma sessão fixa de sete eventos que prova a
  arquitetura inteira sem precisar de nenhum agente de verdade rodando.
- `visual_harness/cli/`: o `vh`, cliente fino sobre a própria API.
- `visual_harness/terminal/`: o avatar desenhando no terminal (TechSpecs
  Seção 4-5, 18-19, 57-59), cliente do mesmo WebSocket que o browser
  consumia. Região reservada por `DECSTBM`, imune ao scroll do agente;
  três modos (`compact`, o padrão: avatar e estado; `full`: painel de
  contexto e linha do tempo também; `minimal`: só o glifo). Trava na
  primeira sessão que aparece, pra não misturar dado de sessões
  diferentes no mesmo overlay; se só existe uma sessão ativa ao
  conectar, hidrata contexto e linha do tempo dela por REST antes de
  qualquer mensagem ao vivo.
- `frontend/`: o avatar SVG original em JavaScript puro, sem build,
  servido pelo próprio backend. TechSpecs Seção 4-5 retirou o browser
  da arquitetura em favor do terminal (`visual_harness/terminal/`
  acima); este diretório fica no repositório por enquanto, mas não é
  mais pra onde o projeto está indo.

## Instalando e rodando

```bash
cd dostoi-mvp
pip install -e .
vh start
```

Num segundo terminal, o avatar no lugar que o projeto está indo agora
(TechSpecs Seção 4-5, veja Arquitetura acima):

```bash
vh watch
vh watch --mode full   # + painel de contexto e linha do tempo
vh watch --mode minimal   # só o glifo, rodapé mínimo
```

Reserva as últimas linhas do terminal pro avatar, estado atual e popup
de Camada 2 quando um checkpoint dispara; o resto da tela continua
rolando normal. Ao conectar, se existir exatamente uma sessão ativa no
backend, o modo `full` busca contexto e linha do tempo dela por REST
antes de mostrar qualquer coisa (uma vez só, nunca em intervalo); com
zero ou mais de uma sessão ativa, a ambiguidade de qual mostrar fica
pra primeira que aparecer ao vivo. `Ctrl+C` sai e devolve o terminal
como estava. Limite conhecido: redimensionar a janela com o `vh watch`
aberto não é tratado, reinicia o comando se isso acontecer.

Pra ver no navegador o avatar SVG antigo (Passo 8, TechSpecs Seção 4-5
já não recomenda mais este caminho, veja a nota em `frontend/` acima):
abra `http://127.0.0.1:8765/` com o backend rodando.

`Ctrl+C` pra parar `vh start` em primeiro plano, ou `vh stop` de outro
terminal se subiu em background (o PID fica salvo em
`~/.visual-harness/server.pid`).

Pra ver funcionando sem plugar em nada ainda:

```bash
vh demo
```

Toca a sessão de demonstração fixa, sete eventos, e o avatar reage
sozinho.

### Configuração (variáveis de ambiente)

| Variável | Padrão | O que faz |
|---|---|---|
| `VH_HOST` | `127.0.0.1` | host que o hook do Claude Code chama |
| `VH_PORT` | `8765` | porta que o hook do Claude Code chama |
| `VH_DISABLE_PERSISTENCE` | desligado (persistência ligada) | qualquer valor desliga a escrita em SQLite |
| `VH_PRIVACY_MODE` | `standard` | `strict` / `standard` / `debug` |
| `VH_JUDGE_BASE_URL` | nenhuma (Camada 2 usa template fixo) | raiz da API compatível com OpenAI do provedor (ex.: `https://api.groq.com/openai/v1`, `https://openrouter.ai/api/v1`, `http://localhost:11434/v1` pro Ollama local) |
| `VH_JUDGE_API_KEY` | nenhuma | chave do provedor acima; sem ela (ou sem `VH_JUDGE_BASE_URL`/`VH_JUDGE_MODEL`) a Camada 2 cai no template fixo |
| `VH_JUDGE_MODEL` | nenhuma | nome do modelo, no formato que o provedor esperar |

Banco em `~/.visual-harness/harness.db`.

## Eventos

Todo evento carrega: `id` (UUIDv7, ordenável no tempo), `session_id`,
`timestamp`, `source`, `type`, `version`, `payload`, `sequence`
(atribuído pelo barramento, não por quem publica). Alguns tipos exigem
campo obrigatório no payload, os únicos com exemplo concreto no
TechSpecs:

| Tipo | Campo obrigatório |
|---|---|
| `file_read`, `file_created`, `file_modified`, `file_deleted`, `file_searched` | `path` |
| `command_started`, `command_finished`, `command_failed` | `command` |
| `test_failed` | `test` |
| `test_suite_completed` | `passed`, `failed` |

Os demais tipos aceitam qualquer payload, porque o próprio TechSpecs
deixa esse schema em aberto.

```bash
vh event --type file_read --path src/main.py --session s1
vh event --type command_started --command "npm test"
```

No PowerShell, o quoting de `--json` não é o que parece óbvio. Testei
até achar o que funciona de verdade:

```powershell
vh event --json '{\"type\": \"test_failed\", \"session_id\": \"s1\", \"source\": \"cli\", \"payload\": {\"test\": \"login\"}}'
```

Aspas simples por fora, `\"` literal por dentro, porque o PowerShell
engole aspas duplas escapadas antes delas chegarem no processo nativo,
mesmo dentro de uma string com crase. Mais simples ainda: usar `--path`
ou `--command` em vez de `--json` sempre que o payload for só isso.

## Plugando no Claude Code

O primeiro adapter real. Duas peças: `translate_hook_event`, função
pura que traduz o payload cru de um hook pro schema de evento comum
(devolve `None` quando não há tipo correspondente, como na delegação
via `Agent`/`Task`, melhor omitir do que forçar um tipo errado), e
`ClaudeCodeAdapter`, que satisfaz o contrato de adapter do sistema.

| Hook | Tool | EventType |
|---|---|---|
| `SessionStart` | — | `agent_started` |
| `Stop` | — | `agent_stopped` |
| `UserPromptSubmit` | — | `user_message` |
| `PreToolUse` | `Bash`/`PowerShell` | `command_started` |
| `PostToolUse` | `Bash`/`PowerShell` | `command_finished` ou `command_failed` |
| `PostToolUse` | `Read` | `file_read` |
| `PostToolUse` | `Glob`/`Grep` | `file_searched` |
| `PostToolUse` | `Edit`/`Write` | `file_modified` |
| `PreToolUse` | `AskUserQuestion`/`ExitPlanMode` | `agent_waiting` |
| qualquer outro | — | nada emitido |

Em `.claude/settings.json` do projeto onde o agente vai codar:

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

O script nunca falha alto: qualquer problema é engolido, porque um hook
quebrado pararia o próprio turno do agente, e isso seria pior que
qualquer avatar mudo. É sucessor do `hooks/emit_event.py` do MVP em
texto original, que só gravava JSONL; este traduz de verdade e fala com
o backend.

## Privacidade

Redação de segredo (`API_KEY`, `TOKEN`, `PASSWORD`, `SECRET`, chave
privada em bloco PEM) acontece só na fronteira de persistência, nunca
no que você vê ao vivo na própria sessão. Três modos: `strict` (nem o
texto redigido sobrevive, payload e contexto ficam vazios antes de
gravar), `standard` (o padrão, segredo trocado por `[REDACTED]`),
`debug` (nada é escondido, e o processo avisa isso explicitamente no
início, em letra maiúscula, porque modo debug com sessão sensível é
exatamente o tipo de decisão que não deveria acontecer por acidente).

## Testando

```bash
pip install -e ".[dev]"
pytest tests
```

Três camadas, como o TechSpecs pede (Seção 53): `tests/unit` (isolado,
mock onde faz sentido), `tests/integration` (componentes de verdade
rodando juntos, sem mock, uma sessão inteira do primeiro evento até o
WebSocket, tudo em processo, via `TestClient`), `tests/e2e` (a mesma
sessão, mas cruzando a fronteira de processo de verdade: `vh event`/`vh
status` fazem HTTP contra um `uvicorn` real numa porta real, o
WebSocket é o cliente `websockets` de verdade, e o avatar de terminal
roda de ponta a ponta contra esse servidor real, com o desenho
capturado num stream em memória em vez do terminal de verdade). A
única perna sem automação é olhar pra tela de verdade, seja o
`vh watch` num terminal real, seja o avatar SVG antigo no navegador;
essa fica pra verificação manual. `tests/fixtures` guarda o dado cru
reaproveitado pelos testes de integração e end-to-end. Duzentos e trinta
e sete testes, todos verdes na última vez que rodei.

Verificação de dependência com `pip-audit`: nenhuma vulnerabilidade
conhecida encontrada.

## MVP em texto original (`dostoi/`)

Antes deste pacote existir, um protótipo mais simples provava a mesma
ideia só em texto, sem servidor, sem SQLite, sem avatar nenhum.
Continua intacto no repositório, standalone:

```bash
python -m dostoi.watch --events ~/.dostoi/events.jsonl
```

O histórico de por que ele existe ao lado do pacote novo está nas
issues #1 a #6, fechadas no dia em que o PRD e o TechSpecs formais
substituíram o escopo original.
