"""Julgamento de Camada 2 (TechSpecs Seção 60.1), em cima do que o
checkpoint capturou. Duas vias, na mesma ordem do protótipo que serviu
de referência (`dostoi/judge.py`):

1. Se `ANTHROPIC_API_KEY` estiver setada e o pacote `anthropic`
   instalado, pede o julgamento de verdade a um modelo pequeno, com o
   contexto já redigido (Seção 43) antes de sair do processo.
2. Senão, cai num template fixo por tipo de checkpoint.

A chamada de rede é sempre feita numa thread separada pelo chamador
(`asyncio.to_thread`), nunca no event loop que atende as outras sessões
(TechSpecs Seção 76: inferência de LLM isolada do event loop).
"""
import os

from visual_harness.humanization.messages import check_message
from visual_harness.privacy.redaction import redact_payload

MODEL = os.environ.get("VH_JUDGE_MODEL", "claude-haiku-4-5-20251001")

_SYSTEM_PROMPT = (
    "Você é a camada metacognitiva de um agente de programação: não faz "
    "o trabalho, observa o que o agente acabou de fazer e comenta sobre "
    "isso em UMA frase curta, primeira pessoa, tom seco e direto. Nunca "
    "cumprimente, nunca explique o óbvio, nunca reivindique experiência "
    "subjetiva (não diga que sente, tem medo ou sofre). Só o julgamento. "
    "Português do Brasil. Sem travessão."
)


def _client():
    try:
        import anthropic
    except ImportError:
        return None
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def _build_user_message(checkpoint_type: str, context: dict) -> str | None:
    if checkpoint_type == "test_failure":
        return (
            f"O comando `{context['command']}` acabou de falhar. "
            "Comente sobre isso em uma frase."
        )
    if checkpoint_type == "rework":
        return (
            f"O arquivo {context['path']} foi editado de novo "
            f"{context['seconds_since']:.0f}s depois da edição anterior. "
            "Comente sobre isso em uma frase."
        )
    return None


def _llm_comment(checkpoint_type: str, context: dict) -> str | None:
    client = _client()
    if client is None:
        return None

    user_msg = _build_user_message(checkpoint_type, context)
    if user_msg is None:
        return None

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=80,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        texto = resp.content[0].text.strip()
        check_message(texto)  # Seção 62: mesmo vindo do LLM, nunca sem guarda
        return texto
    except Exception:  # rede, rate limit, guarda de vocabulário: cai no fallback
        return None


def _fallback_comment(checkpoint_type: str, context: dict) -> str:
    if checkpoint_type == "test_failure":
        return (
            f"o comando falhou ({context['command']!r}), "
            "o que foi feito antes pode não ter resolvido o problema"
        )
    if checkpoint_type == "rework":
        return (
            f"voltou a mexer em {context['path']} pouco tempo depois, "
            "pode ser retrabalho"
        )
    return "checkpoint sem comentário definido"


def comment(checkpoint_type: str, context: dict) -> tuple[str, str]:
    """Redige o contexto (Seção 43) antes de qualquer coisa sair do
    processo, depois tenta o LLM, com fallback de template."""
    context = redact_payload(context)
    texto = _llm_comment(checkpoint_type, context)
    if texto:
        return texto, "llm"
    return _fallback_comment(checkpoint_type, context), "heuristica"
