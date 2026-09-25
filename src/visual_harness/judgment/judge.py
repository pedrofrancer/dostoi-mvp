"""Julgamento de Camada 2 (TechSpecs Seção 60.1), em cima do que o
checkpoint capturou. Duas vias, na mesma ordem do protótipo que serviu
de referência (`dostoi/judge.py`):

1. Se `VH_JUDGE_BASE_URL`, `VH_JUDGE_API_KEY` e `VH_JUDGE_MODEL`
   estiverem setadas, pede o julgamento de verdade a um modelo, com o
   contexto já redigido (Seção 43) antes de sair do processo. Cliente
   HTTP genérico contra qualquer endpoint `/chat/completions`
   compatível com OpenAI (Groq, OpenRouter, Cerebras, Ollama local, o
   que o usuário já tiver rodando o próprio agente de código através
   de OpenCode/outro CLI), não um SDK de um provedor só.
2. Senão, cai num template fixo por tipo de checkpoint.

A chamada de rede é sempre feita numa thread separada pelo chamador
(`asyncio.to_thread`), nunca no event loop que atende as outras sessões
(TechSpecs Seção 76: inferência de LLM isolada do event loop).
"""
import os

import httpx

from visual_harness.humanization.messages import check_message
from visual_harness.privacy.redaction import redact_payload

REQUEST_TIMEOUT_SECONDS = 15.0

_SYSTEM_PROMPT = (
    "Você é a camada metacognitiva de um agente de programação: não faz "
    "o trabalho, observa o que o agente acabou de fazer e comenta sobre "
    "isso em UMA frase curta, primeira pessoa, tom seco e direto. Nunca "
    "cumprimente, nunca explique o óbvio, nunca reivindique experiência "
    "subjetiva (não diga que sente, tem medo ou sofre). Só o julgamento. "
    "Português do Brasil. Sem travessão."
)


def _provider_config() -> tuple[str, str, str] | None:
    base_url = os.environ.get("VH_JUDGE_BASE_URL")
    api_key = os.environ.get("VH_JUDGE_API_KEY")
    model = os.environ.get("VH_JUDGE_MODEL")
    if not base_url or not api_key or not model:
        return None
    return base_url.rstrip("/"), api_key, model


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
    config = _provider_config()
    if config is None:
        return None
    base_url, api_key, model = config

    user_msg = _build_user_message(checkpoint_type, context)
    if user_msg is None:
        return None

    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "max_tokens": 80,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        texto = response.json()["choices"][0]["message"]["content"].strip()
        check_message(texto)  # Seção 62: mesmo vindo do LLM, nunca sem guarda
        return texto
    except Exception:  # rede, provedor fora do ar, formato inesperado, guarda de vocabulario
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
