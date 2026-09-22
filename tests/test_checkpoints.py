import unittest

from dostoi import checkpoints


class TestDetect(unittest.TestCase):
    def test_bash_failure_triggers_test_failure(self):
        event = {
            "hook": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest"},
            "tool_response": {"is_error": True},
        }
        achados = checkpoints.detect(event, history=[])
        tipos = [tipo for tipo, _ in achados]
        self.assertIn("test_failure", tipos)

    def test_bash_success_triggers_nothing(self):
        event = {
            "hook": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest"},
            "tool_response": {"is_error": False},
        }
        achados = checkpoints.detect(event, history=[])
        self.assertEqual(achados, [])

    def test_reedit_same_file_within_window_triggers_rework(self):
        primeira_edicao = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
            "ts": 1000.0,
        }
        segunda_edicao = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
            "ts": 1100.0,
        }
        achados = checkpoints.detect(segunda_edicao, history=[primeira_edicao])
        tipos = [tipo for tipo, _ in achados]
        self.assertIn("rework", tipos)

    def test_reedit_different_file_does_not_trigger_rework(self):
        primeira_edicao = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
            "ts": 1000.0,
        }
        edicao_outro_arquivo = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/bar.py"},
            "ts": 1100.0,
        }
        achados = checkpoints.detect(edicao_outro_arquivo, history=[primeira_edicao])
        self.assertEqual(achados, [])

    def test_reedit_outside_window_does_not_trigger_rework(self):
        primeira_edicao = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
            "ts": 1000.0,
        }
        edicao_tardia = {
            "hook": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
            "ts": 1000.0 + checkpoints.REWORK_WINDOW_SECONDS + 1,
        }
        achados = checkpoints.detect(edicao_tardia, history=[primeira_edicao])
        self.assertEqual(achados, [])


if __name__ == "__main__":
    unittest.main()
