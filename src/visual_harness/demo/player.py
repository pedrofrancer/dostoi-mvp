"""Player de eventos de demo (TechSpecs Seção 51-52): toca o fixture
`examples/demo_session.json` pelo `EventBus` real, no ritmo configurável
por `speed`. Nenhum caminho visual separado; é o mesmo pipeline do
agente de verdade, só que a fonte dos eventos é um arquivo, não um hook.
"""
import asyncio
import json
from enum import Enum
from pathlib import Path

from visual_harness.events.bus import EventBus
from visual_harness.events.models import Event
from visual_harness.events.types import EventType

DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[3] / "examples" / "demo_session.json"
DEFAULT_STEP_DELAY_S = 1.0


class DemoState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


def load_fixture(path: Path = DEFAULT_FIXTURE_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class DemoPlayer:
    def __init__(
        self,
        bus: EventBus,
        fixture: list[dict] | None = None,
        session_id: str = "demo",
        step_delay_s: float = DEFAULT_STEP_DELAY_S,
    ) -> None:
        self._bus = bus
        self._fixture = fixture if fixture is not None else load_fixture()
        self._session_id = session_id
        self._step_delay_s = step_delay_s
        self._speed = 1.0
        self._index = 0
        self.state = DemoState.IDLE
        self._task: asyncio.Task | None = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    def set_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ValueError("speed precisa ser positivo")
        self._speed = speed

    def reset(self) -> None:
        if self.state == DemoState.RUNNING:
            raise RuntimeError("chame stop() antes de reset() enquanto o demo roda")
        self._index = 0
        self.state = DemoState.IDLE

    async def start(self) -> None:
        if self.state == DemoState.RUNNING:
            return
        self.state = DemoState.RUNNING
        self._pause_event.set()
        self._task = asyncio.create_task(self._run())

    def pause(self) -> None:
        if self.state == DemoState.RUNNING:
            self.state = DemoState.PAUSED
            self._pause_event.clear()

    def resume(self) -> None:
        if self.state == DemoState.PAUSED:
            self.state = DemoState.RUNNING
            self._pause_event.set()

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self.state = DemoState.IDLE
        self._index = 0

    async def _run(self) -> None:
        while self._index < len(self._fixture):
            await self._pause_event.wait()
            item = self._fixture[self._index]
            event = Event(
                session_id=self._session_id,
                source="demo",
                type=EventType(item["type"]),
                payload=item.get("payload", {}),
            )
            await self._bus.publish(event)
            self._index += 1
            if self._index < len(self._fixture):
                await asyncio.sleep(self._step_delay_s / self._speed)
        self.state = DemoState.FINISHED
