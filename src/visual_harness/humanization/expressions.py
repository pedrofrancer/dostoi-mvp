"""Conjunto inicial de expressões (TechSpecs Seção 27). Pequeno de
propósito: expressão é composável, não um asset por estado.
"""
from enum import Enum


class Expression(str, Enum):
    NEUTRAL = "neutral"
    FOCUSED = "focused"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    CONCERNED = "concerned"
    SURPRISED = "surprised"
    RELIEVED = "relieved"
    SATISFIED = "satisfied"
    ATTENTIVE = "attentive"
    WAITING = "waiting"
