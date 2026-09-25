"""Unidade (TechSpecs Seção 60.1): os dois gatilhos de checkpoint sobre
o modelo de `Event` comum, o mesmo par calibrado em
`dostoi/checkpoints.py`.
"""
import unittest
from datetime import datetime, timedelta, timezone

from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.judgment.checkpoints import detect


def _event(event_type, payload=None, seconds_offset=0, session_id="s1"):
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds_offset)
    return Event(
        session_id=session_id,
        source="test",
        type=event_type,
        payload=payload or {},
        timestamp=ts,
    )


class TestCommandFailureCheckpoint(unittest.TestCase):
    def test_command_failed_is_a_checkpoint(self):
        event = _event(EventType.COMMAND_FAILED, {"command": "pytest"})
        achados = detect(event, history=[])
        self.assertEqual(achados, [("test_failure", {"command": "pytest"})])

    def test_test_failed_is_a_checkpoint(self):
        event = _event(EventType.TEST_FAILED, {"test": "test_login"})
        achados = detect(event, history=[])
        self.assertEqual(achados, [("test_failure", {"command": "test_login"})])

    def test_command_finished_is_not_a_checkpoint(self):
        event = _event(EventType.COMMAND_FINISHED, {"command": "pytest"})
        self.assertEqual(detect(event, history=[]), [])


class TestReworkCheckpoint(unittest.TestCase):
    def test_second_edit_of_same_file_within_window_is_rework(self):
        first = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=0)
        second = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=30)

        achados = detect(second, history=[first])

        self.assertEqual(len(achados), 1)
        tipo, contexto = achados[0]
        self.assertEqual(tipo, "rework")
        self.assertEqual(contexto["path"], "src/auth.py")
        self.assertEqual(contexto["seconds_since"], 30.0)

    def test_edit_of_different_file_is_not_rework(self):
        first = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=0)
        second = _event(EventType.FILE_MODIFIED, {"path": "src/other.py"}, seconds_offset=30)
        self.assertEqual(detect(second, history=[first]), [])

    def test_edit_outside_window_is_not_rework(self):
        first = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=0)
        second = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=301)
        self.assertEqual(detect(second, history=[first]), [])

    def test_first_edit_of_a_file_is_not_rework(self):
        event = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"})
        self.assertEqual(detect(event, history=[]), [])

    def test_file_created_does_not_count_as_prior_edit(self):
        # calibrado igual ao prototipo: so Edit/Write (FILE_MODIFIED)
        # conta pra retrabalho, um FILE_CREATED antes nao dispara.
        first = _event(EventType.FILE_CREATED, {"path": "src/auth.py"}, seconds_offset=0)
        second = _event(EventType.FILE_MODIFIED, {"path": "src/auth.py"}, seconds_offset=30)
        self.assertEqual(detect(second, history=[first]), [])


if __name__ == "__main__":
    unittest.main()
