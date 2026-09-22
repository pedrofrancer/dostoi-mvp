import unittest

from visual_harness.adapters.claude_code import (
    CLAUDE_CODE_CAPABILITIES,
    ClaudeCodeAdapter,
    translate_hook_event,
)
from visual_harness.events.types import EventType


class TestTranslateHookEvent(unittest.TestCase):
    def test_session_start_becomes_agent_started(self):
        event = translate_hook_event({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertEqual(event.type, EventType.AGENT_STARTED)
        self.assertEqual(event.session_id, "s1")
        self.assertEqual(event.source, "claude-code")

    def test_stop_becomes_agent_stopped(self):
        event = translate_hook_event({"hook_event_name": "Stop", "session_id": "s1"})
        self.assertEqual(event.type, EventType.AGENT_STOPPED)

    def test_user_prompt_submit_with_prompt_carries_text(self):
        event = translate_hook_event(
            {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "faz X"}
        )
        self.assertEqual(event.type, EventType.USER_MESSAGE)
        self.assertEqual(event.payload["text"], "faz X")

    def test_user_prompt_submit_without_prompt_has_empty_payload(self):
        event = translate_hook_event({"hook_event_name": "UserPromptSubmit", "session_id": "s1"})
        self.assertEqual(event.type, EventType.USER_MESSAGE)
        self.assertNotIn("text", event.payload)

    def test_pre_tool_use_bash_becomes_command_started(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PreToolUse",
                "session_id": "s1",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
            }
        )
        self.assertEqual(event.type, EventType.COMMAND_STARTED)
        self.assertEqual(event.payload["command"], "pytest")

    def test_post_tool_use_bash_success_becomes_command_finished(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
                "tool_response": {"is_error": False},
            }
        )
        self.assertEqual(event.type, EventType.COMMAND_FINISHED)

    def test_post_tool_use_bash_error_becomes_command_failed(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
                "tool_response": {"is_error": True},
            }
        )
        self.assertEqual(event.type, EventType.COMMAND_FAILED)

    def test_post_tool_use_read_becomes_file_read(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Read",
                "tool_input": {"file_path": "src/main.py"},
            }
        )
        self.assertEqual(event.type, EventType.FILE_READ)
        self.assertEqual(event.payload["path"], "src/main.py")

    def test_post_tool_use_grep_becomes_file_searched(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Grep",
                "tool_input": {"pattern": "def foo"},
            }
        )
        self.assertEqual(event.type, EventType.FILE_SEARCHED)
        self.assertEqual(event.payload["path"], "def foo")

    def test_post_tool_use_edit_becomes_file_modified(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Edit",
                "tool_input": {"file_path": "src/main.py"},
            }
        )
        self.assertEqual(event.type, EventType.FILE_MODIFIED)

    def test_post_tool_use_write_becomes_file_modified(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Write",
                "tool_input": {"file_path": "src/new.py"},
            }
        )
        self.assertEqual(event.type, EventType.FILE_MODIFIED)

    def test_pre_tool_use_ask_user_question_becomes_agent_waiting(self):
        event = translate_hook_event(
            {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "AskUserQuestion"}
        )
        self.assertEqual(event.type, EventType.AGENT_WAITING)

    def test_missing_session_id_returns_none(self):
        event = translate_hook_event({"hook_event_name": "SessionStart"})
        self.assertIsNone(event)

    def test_unmapped_tool_returns_none(self):
        event = translate_hook_event(
            {
                "hook_event_name": "PreToolUse",
                "session_id": "s1",
                "tool_name": "Agent",
            }
        )
        self.assertIsNone(event)

    def test_unknown_hook_name_returns_none(self):
        event = translate_hook_event({"hook_event_name": "SomethingElse", "session_id": "s1"})
        self.assertIsNone(event)


class TestClaudeCodeAdapterCapabilities(unittest.TestCase):
    def test_capabilities_reflect_what_is_actually_observed(self):
        caps = ClaudeCodeAdapter().capabilities()
        self.assertIs(caps, CLAUDE_CODE_CAPABILITIES)
        self.assertTrue(caps.tool_events)
        self.assertTrue(caps.file_events)
        self.assertTrue(caps.command_events)
        self.assertTrue(caps.user_messages)
        self.assertTrue(caps.structured_output)
        # sem sinal estruturado de teste, sem acesso a plano/raciocinio
        self.assertFalse(caps.test_events)
        self.assertFalse(caps.planning_events)


class TestClaudeCodeAdapterLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_health_before_start_is_unhealthy(self):
        adapter = ClaudeCodeAdapter()
        health = await adapter.health()
        self.assertFalse(health.healthy)

    async def test_health_after_start_is_healthy(self):
        adapter = ClaudeCodeAdapter()
        await adapter.start()
        health = await adapter.health()
        self.assertTrue(health.healthy)

    async def test_health_after_stop_is_unhealthy_again(self):
        adapter = ClaudeCodeAdapter()
        await adapter.start()
        await adapter.stop()
        health = await adapter.health()
        self.assertFalse(health.healthy)


if __name__ == "__main__":
    unittest.main()
