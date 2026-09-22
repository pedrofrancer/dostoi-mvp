import unittest

from visual_harness.events.bus import EventBus
from visual_harness.events.models import Event
from visual_harness.events.types import EventType


def make_event(session_id="sess_1", **overrides):
    data = dict(session_id=session_id, source="claude-code", type=EventType.AGENT_STARTED)
    data.update(overrides)
    return Event(**data)


class TestEventBus(unittest.IsolatedAsyncioTestCase):
    async def test_publish_calls_subscribed_handlers(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(handler)
        event = make_event()
        await bus.publish(event)

        self.assertEqual(received, [event])

    async def test_unsubscribe_stops_receiving(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        subscription = bus.subscribe(handler)
        subscription.unsubscribe()
        await bus.publish(make_event())

        self.assertEqual(received, [])

    async def test_sequence_assigned_when_missing(self):
        bus = EventBus()
        first = make_event()
        second = make_event()

        await bus.publish(first)
        await bus.publish(second)

        self.assertEqual(first.sequence, 1)
        self.assertEqual(second.sequence, 2)

    async def test_sequence_independent_per_session(self):
        bus = EventBus()
        a1 = make_event(session_id="sess_a")
        b1 = make_event(session_id="sess_b")
        a2 = make_event(session_id="sess_a")

        await bus.publish(a1)
        await bus.publish(b1)
        await bus.publish(a2)

        self.assertEqual(a1.sequence, 1)
        self.assertEqual(b1.sequence, 1)
        self.assertEqual(a2.sequence, 2)

    async def test_existing_sequence_is_not_overwritten(self):
        bus = EventBus()
        event = make_event(sequence=42)

        await bus.publish(event)

        self.assertEqual(event.sequence, 42)

    async def test_order_preserved_within_session(self):
        bus = EventBus()
        events = [make_event() for _ in range(5)]

        for event in events:
            await bus.publish(event)

        self.assertEqual([e.sequence for e in events], [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
