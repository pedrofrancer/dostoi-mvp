"""Resume uma lista de eventos num SessionContext (TechSpecs Seção 19).
Agregação simples, sem estado próprio: recalculável a qualquer momento
a partir do histórico de eventos da sessão.
"""
from visual_harness.context.models import SessionContext
from visual_harness.events.models import Event
from visual_harness.events.types import EventType
from visual_harness.state.engine import derive_state

MAX_RECENT_ERRORS = 10


def compute_context(events: list[Event], agent: str) -> SessionContext:
    task: str | None = None
    modified_files: list[str] = []
    tests_passed = 0
    tests_failed = 0
    recent_errors: list[str] = []

    for event in events:
        if event.type in (EventType.TASK_STARTED, EventType.TASK_CHANGED):
            description = event.payload.get("description")
            if description:
                task = description

        elif event.type in (EventType.FILE_CREATED, EventType.FILE_MODIFIED):
            path = event.payload.get("path")
            if path and path not in modified_files:
                modified_files.append(path)

        elif event.type == EventType.TEST_PASSED:
            tests_passed += 1
        elif event.type == EventType.TEST_FAILED:
            tests_failed += 1
            test_name = event.payload.get("test", "teste sem nome")
            recent_errors.append(f"falha: {test_name}")
        elif event.type == EventType.TEST_SUITE_COMPLETED:
            tests_passed += event.payload.get("passed", 0)
            tests_failed += event.payload.get("failed", 0)

        elif event.type == EventType.AGENT_ERROR:
            message = event.payload.get("message", "erro sem detalhe")
            recent_errors.append(message)

    return SessionContext(
        agent=agent,
        current_state=derive_state(events),
        task=task,
        modified_files=modified_files,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        recent_errors=recent_errors[-MAX_RECENT_ERRORS:],
    )
