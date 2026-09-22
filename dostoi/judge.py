"""Camada 2: transforma um checkpoint detectado num comentário curto e
reflexivo. Duas vias, na ordem:

1. Se ANTHROPIC_API_KEY estiver setada e o pacote `anthropic` instalado,
   pede o julgamento de verdade a um modelo pequeno, no contexto do
   checkpoint.
2. Senão, cai num template fixo por tipo de checkpoint, claramente
   rotulado como heurística, nunca fingindo ser mais do que é.
"""
import os

MODEL = os.environ.get("DOSTOI_JUDGE_MODEL", "claude-haiku-4-5-20251001")

_SYSTEM_PROMPT = (
    "Você é a camada metacognitiva de um agente de programação: não faz o "
    "trabalho, observa o que o agente acabou de fazer e comenta sobre isso "
    "em UMA frase curta, primeira pessoa, tom seco e direto. Nunca "
    "cumprimente, nunca explique o óbvio, só o julgamento. Português do "
    "Brasil. Sem travessão."
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


def _llm_comment(checkpoint_type, context):
    client = _client()
    if client is None:
        return None
    if checkpoint_type == "test_failure":
        user_msg = (
            f"O comando `{context['command']}` acabou de falhar. "
            "Comente sobre isso em uma frase."
        )
    elif checkpoint_type == "rework":
        user_msg = (
            f"O arquivo {context['file_path']} foi editado de novo "
            f"{context['seconds_since']:.0f}s depois da edição anterior. "
            "Comente sobre isso em uma frase."
        )
    else:
        return None

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=80,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        return resp.content[0].text.strip()
    except Exception:  # rede, rate limit, o que for: cai no fallback
        return None


def _fallback_comment(checkpoint_type, context):
    if checkpoint_type == "test_failure":
        return (
            f"o comando falhou ({context['command']!r}), "
            "o que fiz antes pode não ter resolvido o problema"
        )
    if checkpoint_type == "rework":
        return (
            f"voltei a mexer em {context['file_path']} pouco tempo depois, "
            "pode ser retrabalho"
        )
    return "checkpoint sem comentário definido"


def comment(checkpoint_type, context):
    texto = _llm_comment(checkpoint_type, context)
    if texto:
        return texto, "llm"
    return _fallback_comment(checkpoint_type, context), "heuristica"
