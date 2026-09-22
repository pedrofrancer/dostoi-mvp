"""Barramento de eventos assíncrono (TechSpecs Seção 11). O publish
também cuida da ordenação por sessão (Seção 12): quem chama não precisa
saber que número de sequência o evento vai receber.
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable

from visual_harness.events.models import Event

EventHandler = Callable[[Event], Awaitable[None]]


@dataclass(eq=False)
class Subscription:
    _bus: "EventBus"
    _callback: EventHandler

    def unsubscribe(self) -> None:
        self._bus.unsubscribe(self)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscription] = []
        self._sequence_by_session: dict[str, int] = defaultdict(int)
        self._sequence_lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        if event.sequence is None:
            async with self._sequence_lock:
                self._sequence_by_session[event.session_id] += 1
                event.sequence = self._sequence_by_session[event.session_id]
        for subscription in list(self._subscribers):
            await subscription._callback(event)

    def subscribe(self, callback: EventHandler) -> Subscription:
        subscription = Subscription(self, callback)
        self._subscribers.append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        if subscription in self._subscribers:
            self._subscribers.remove(subscription)
