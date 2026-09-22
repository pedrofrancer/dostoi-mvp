import asyncio
import unittest

from visual_harness.demo.player import DemoPlayer, DemoState, load_fixture
from visual_harness.events.bus import EventBus
from visual_harness.state.engine import derive_state
from visual_harness.state.models import AgentState

FIXTURE_TYPES = [
    "task_started",
    "file_read",
    "command_started",
    "test_failed",
    "user_correction",
    "approach_changed",
    "test_suite_completed",
]


async def _wait_until_finished(player: DemoPlayer, timeout_s: float = 2.0) -> None:
    elapsed = 0.0
    step = 0.01
    while player.state != DemoState.FINISHED and elapsed < timeout_s:
        await asyncio.sleep(step)
        elapsed += step
    if player.state != DemoState.FINISHED:
        raise AssertionError("demo não terminou dentro do timeout do teste")


class TestLoadFixture(unittest.TestCase):
    def test_fixture_has_seven_events_in_order(self):
        fixture = load_fixture()
        self.assertEqual([item["type"] for item in fixture], FIXTURE_TYPES)


class TestDemoPlayer(unittest.IsolatedAsyncioTestCase):
    async def test_start_publishes_all_events_through_bus_in_order(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(handler)
        player = DemoPlayer(bus, step_delay_s=0.01)

        await player.start()
        await _wait_until_finished(player)

        self.assertEqual([e.type.value for e in received], FIXTURE_TYPES)

    async def test_demo_sequence_derives_expected_final_state(self):
        # Achado, não suposição: o fixture não tem agent_completed, só
        # test_suite_completed, então a cascata do Step 4 não fecha em
        # SUCCESS aqui. Fica registrado como está, não forçado.
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(handler)
        player = DemoPlayer(bus, step_delay_s=0.01)

        await player.start()
        await _wait_until_finished(player)

        self.assertEqual(derive_state(received), AgentState.RECONSIDERING)

    async def test_pause_stops_emission_until_resumed(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(handler)
        player = DemoPlayer(bus, step_delay_s=0.05)

        await player.start()
        await asyncio.sleep(0.02)  # deixa o primeiro evento sair
        player.pause()
        count_while_paused = len(received)
        await asyncio.sleep(0.15)
        self.assertEqual(len(received), count_while_paused)

        player.resume()
        await _wait_until_finished(player)
        self.assertEqual(len(received), len(FIXTURE_TYPES))

    async def test_stop_cancels_and_resets_index(self):
        bus = EventBus()
        player = DemoPlayer(bus, step_delay_s=0.05)

        await player.start()
        await asyncio.sleep(0.02)
        await player.stop()

        self.assertEqual(player.state, DemoState.IDLE)
        player.reset()  # não deve levantar: já não está rodando

    def test_set_speed_rejects_non_positive(self):
        player = DemoPlayer(EventBus(), step_delay_s=0.01)
        with self.assertRaises(ValueError):
            player.set_speed(0)
        with self.assertRaises(ValueError):
            player.set_speed(-1)

    async def test_reset_while_running_raises(self):
        bus = EventBus()
        player = DemoPlayer(bus, step_delay_s=0.05)
        await player.start()
        with self.assertRaises(RuntimeError):
            player.reset()
        await player.stop()


if __name__ == "__main__":
    unittest.main()
