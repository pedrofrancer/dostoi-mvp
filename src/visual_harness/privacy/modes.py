"""Modos de privacidade (TechSpecs Seção 44): decide o que sobrevive
até a persistência, não o que aparece ao vivo.
"""
from enum import Enum

from visual_harness.context.models import SessionContext
from visual_harness.events.models import Event
from visual_harness.privacy.redaction import redact_payload, redact_text


class PrivacyMode(str, Enum):
    STRICT = "strict"
    STANDARD = "standard"
    DEBUG = "debug"


def prepare_event_for_persistence(event: Event, mode: PrivacyMode) -> Event:
    if mode == PrivacyMode.STRICT:
        return event.model_copy(update={"payload": {}})
    if mode == PrivacyMode.STANDARD:
        return event.model_copy(update={"payload": redact_payload(event.payload)})
    return event  # DEBUG: sem redação, quem ligou isso já foi avisado


def prepare_context_for_persistence(context: SessionContext, mode: PrivacyMode) -> SessionContext:
    if mode == PrivacyMode.STRICT:
        return context.model_copy(update={"task": None, "recent_errors": []})
    if mode == PrivacyMode.STANDARD:
        return context.model_copy(
            update={
                "task": redact_text(context.task) if context.task else None,
                "recent_errors": [redact_text(e) for e in context.recent_errors],
            }
        )
    return context
