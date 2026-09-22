"""Contrato de adapter (TechSpecs Seção 13-14). O núcleo do sistema
nunca depende de um provider específico; só desse contrato.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class AdapterCapabilities:
    tool_events: bool
    file_events: bool
    command_events: bool
    test_events: bool
    user_messages: bool
    planning_events: bool
    structured_output: bool


@dataclass
class AdapterHealth:
    healthy: bool
    detail: str = ""


class AgentAdapter(Protocol):
    name: str

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def health(self) -> AdapterHealth: ...

    def capabilities(self) -> AdapterCapabilities: ...
