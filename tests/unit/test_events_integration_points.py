from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from core.events import event_bus
from services.task_service import task_service
from tasks.executor import task_executor


async def test_push_to_dlq_emits_task_failed_event() -> None:
    session = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock(
        side_effect=lambda target: setattr(target, "id", "dlq-1")
    )
    original = event_bus.emit
    mocked_emit = AsyncMock()
    event_bus.emit = mocked_emit

    try:
        await task_service.push_to_dlq(
            session,
            task_name="broken-task",
            payload={"step": 1},
            error_message="boom",
        )
    finally:
        event_bus.emit = original

    mocked_emit.assert_awaited_once()
    assert mocked_emit.await_args.kwargs["event_type"] == "task.failed"


async def test_complete_run_emits_task_completed_event() -> None:
    session = AsyncMock()
    task = SimpleNamespace(
        id="task-1", project_id="project-1", session_id=None, status="running"
    )
    task_run = SimpleNamespace(id="run-1", status="running", output_payload={})
    original = event_bus.emit
    mocked_emit = AsyncMock()
    event_bus.emit = mocked_emit

    try:
        await task_executor.complete_run(
            session,
            task=task,
            task_run=task_run,
            output_payload={"content": "done"},
        )
    finally:
        event_bus.emit = original

    mocked_emit.assert_awaited_once()
    assert mocked_emit.await_args.kwargs["event_type"] == "task.completed"
