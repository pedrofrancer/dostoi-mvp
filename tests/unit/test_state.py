import unittest

from dostoi import state


class TestClassify(unittest.TestCase):
    def test_session_start_is_idle(self):
        estado, _ = state.classify({"hook": "SessionStart"})
        self.assertEqual(estado, state.STATE_IDLE)

    def test_read_tool_is_reading(self):
        event = {
            "hook": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "src/foo.py"},
        }
        estado, detalhe = state.classify(event)
        self.assertEqual(estado, state.STATE_READING)
        self.assertEqual(detalhe, "src/foo.py")

    def test_edit_tool_is_editing(self):
        event = {
            "hook": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/foo.py"},
        }
        estado, _ = state.classify(event)
        self.assertEqual(estado, state.STATE_EDITING)

    def test_bash_tool_is_running(self):
        event = {
            "hook": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest"},
        }
        estado, detalhe = state.classify(event)
        self.assertEqual(estado, state.STATE_RUNNING)
        self.assertEqual(detalhe, "pytest")

    def test_post_tool_use_error_overrides_tool_state(self):
        event = {
            "hook": "PostToolUse",
            "tool_name": "Bash",
            "tool_response": {"is_error": True},
        }
        estado, _ = state.classify(event)
        self.assertEqual(estado, state.STATE_ERROR)

    def test_post_tool_use_without_error_keeps_tool_state(self):
        event = {
            "hook": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest"},
            "tool_response": {"is_error": False},
        }
        estado, _ = state.classify(event)
        self.assertEqual(estado, state.STATE_RUNNING)

    def test_unknown_tool_falls_back_to_working(self):
        event = {"hook": "PreToolUse", "tool_name": "SomeFutureTool"}
        estado, detalhe = state.classify(event)
        self.assertEqual(estado, state.STATE_WORKING)
        self.assertEqual(detalhe, "SomeFutureTool")

    def test_stop_hook_is_idle(self):
        estado, _ = state.classify({"hook": "Stop"})
        self.assertEqual(estado, state.STATE_IDLE)


if __name__ == "__main__":
    unittest.main()
