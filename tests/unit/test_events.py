import unittest
import uuid
from datetime import datetime, timezone

from pydantic import ValidationError

from visual_harness.events.models import Event
from visual_harness.events.types import EventType


def base(**overrides):
    data = dict(session_id="sess_1", source="claude-code", type=EventType.AGENT_STARTED)
    data.update(overrides)
    return data


class TestEvent(unittest.TestCase):
    def test_id_defaults_to_uuid7_string(self):
        event = Event(**base())
        self.assertEqual(uuid.UUID(event.id).version, 7)

    def test_timestamp_defaults_to_now_utc(self):
        before = datetime.now(timezone.utc)
        event = Event(**base())
        after = datetime.now(timezone.utc)
        self.assertLessEqual(before, event.timestamp)
        self.assertLessEqual(event.timestamp, after)

    def test_version_defaults_to_1(self):
        self.assertEqual(Event(**base()).version, 1)

    def test_payload_defaults_to_empty_dict(self):
        self.assertEqual(Event(**base()).payload, {})

    def test_file_read_requires_path(self):
        with self.assertRaises(ValidationError):
            Event(**base(type=EventType.FILE_READ))

    def test_file_read_with_path_is_valid(self):
        event = Event(**base(type=EventType.FILE_READ, payload={"path": "src/main.py"}))
        self.assertEqual(event.payload["path"], "src/main.py")

    def test_command_started_requires_command(self):
        with self.assertRaises(ValidationError):
            Event(**base(type=EventType.COMMAND_STARTED))

    def test_test_suite_completed_requires_passed_and_failed(self):
        with self.assertRaises(ValidationError):
            Event(**base(type=EventType.TEST_SUITE_COMPLETED, payload={"passed": 33}))

    def test_test_suite_completed_with_both_fields_is_valid(self):
        event = Event(
            **base(
                type=EventType.TEST_SUITE_COMPLETED,
                payload={"passed": 33, "failed": 0},
            )
        )
        self.assertEqual(event.payload["failed"], 0)

    def test_type_without_required_schema_accepts_any_payload(self):
        event = Event(**base(type=EventType.AGENT_MESSAGE, payload={"anything": True}))
        self.assertTrue(event.payload["anything"])


if __name__ == "__main__":
    unittest.main()
