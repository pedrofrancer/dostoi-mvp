"""Redação de segredo (TechSpecs Seção 43). Roda antes de qualquer
persistência, nunca no caminho ao vivo (memória, WebSocket, API): a
sessão que você mesmo está observando na hora não precisa de segredo
escondido de si mesma, só o que fica gravado em disco precisa.
"""
import re

REDACTED = "[REDACTED]"

_KEY_VALUE_PATTERN = re.compile(
    r"(?i)\b(API_KEY|APIKEY|TOKEN|ACCESS_TOKEN|SECRET|PASSWORD|PASS|PRIVATE_KEY)"
    r"(\s*[:=]\s*)([^\s,;\"']+)"
)

_PEM_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")


def redact_text(text: str) -> str:
    text = _PEM_PATTERN.sub(REDACTED, text)
    text = _KEY_VALUE_PATTERN.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", text)
    return text


def redact_value(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {key: redact_value(v) for key, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v) for v in value]
    return value


def redact_payload(payload: dict) -> dict:
    return redact_value(payload)
