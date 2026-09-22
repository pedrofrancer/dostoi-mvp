"""Tipos de evento canônicos (TechSpecs Seção 9). Agrupados por
categoria só pra leitura; no modelo são um enum só, sem hierarquia.
"""
from enum import Enum


class EventType(str, Enum):
    # Agent
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_MESSAGE = "agent_message"
    AGENT_ERROR = "agent_error"
    AGENT_WAITING = "agent_waiting"
    AGENT_COMPLETED = "agent_completed"

    # Tool
    TOOL_STARTED = "tool_started"
    TOOL_FINISHED = "tool_finished"
    TOOL_FAILED = "tool_failed"

    # File
    FILE_READ = "file_read"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_SEARCHED = "file_searched"

    # Command
    COMMAND_STARTED = "command_started"
    COMMAND_FINISHED = "command_finished"
    COMMAND_FAILED = "command_failed"

    # Test
    TEST_STARTED = "test_started"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    TEST_SUITE_COMPLETED = "test_suite_completed"

    # User
    USER_MESSAGE = "user_message"
    USER_CORRECTION = "user_correction"
    USER_APPROVAL = "user_approval"
    USER_REJECTION = "user_rejection"
    USER_REQUIREMENT_CHANGE = "user_requirement_change"
    USER_CONFIRMATION = "user_confirmation"
    USER_INTERRUPT = "user_interrupt"

    # Context
    TASK_STARTED = "task_started"
    TASK_CHANGED = "task_changed"
    APPROACH_DETECTED = "approach_detected"
    APPROACH_CHANGED = "approach_changed"
    CONTEXT_UPDATED = "context_updated"
