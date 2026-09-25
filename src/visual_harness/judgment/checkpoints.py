"""Detecta os checkpoints que merecem julgamento de Camada 2 (TechSpecs
Seção 60.1). Mesmos dois gatilhos calibrados no protótipo
`dostoi/checkpoints.py` (falha de comando/teste, retrabalho no mesmo
arquivo), portados do payload cru de hook pro modelo de `Event` comum
que o EventBus já usa.
"""
from visual_harness.events.models import Event
from visual_harness.events.types import EventType

REWORK_WINDOW_SECONDS = 300
REWORK_LOOKBACK = 8

_FAILURE_TYPES = (EventType.COMMAND_FAILED, EventType.TEST_FAILED)
_EDIT_TYPES = (EventType.FILE_MODIFIED,)


def detect(event: Event, history: list[Event]) -> list[tuple[str, dict]]:
    """event: o evento que acabou de chegar. history: eventos anteriores
    da mesma sessão, mais recente por último, sem incluir `event`.

    Devolve uma lista de (tipo_checkpoint, contexto); geralmente 0 ou 1
    item, mas nada impede mais de um no mesmo evento.
    """
    achados: list[tuple[str, dict]] = []

    if event.type in _FAILURE_TYPES:
        comando = event.payload.get("command") or event.payload.get("test", "")
        achados.append(("test_failure", {"command": comando}))

    if event.type in _EDIT_TYPES:
        alvo = event.payload.get("path")
        if alvo:
            janela = history[-REWORK_LOOKBACK:]
            for anterior in reversed(janela):
                if anterior.type not in _EDIT_TYPES:
                    continue
                if anterior.payload.get("path") != alvo:
                    continue
                delta = (event.timestamp - anterior.timestamp).total_seconds()
                if 0 <= delta <= REWORK_WINDOW_SECONDS:
                    achados.append(("rework", {"path": alvo, "seconds_since": delta}))
                break

    return achados
