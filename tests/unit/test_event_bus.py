from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from core.events import EventBus


async def test_emit_logs_event_without_matching_subscriptions() -> None:
    bus = EventBus()
    session = AsyncMock()
    created_event = SimpleNamespace(id="evt-1")
    bus._matching_subscriptions = AsyncMock(return_value=[])
    bus._create_event = AsyncMock(return_value=created_event)

    event = await bus.emit(
        session,
        event_type="task.completed",
        payload={"project_id": "project-1"},
    )

    assert event is created_event
    bus._create_event.assert_awaited_once()


async def test_emit_fans_out_to_matching_subscriptions() -> None:
    bus = EventBus()
    session = AsyncMock()
    sub1 = SimpleNamespace(id="sub-1")
    sub2 = SimpleNamespace(id="sub-2")
    first_event = SimpleNamespace(id="evt-1")
    second_event = SimpleNamespace(id="evt-2")
    bus._matching_subscriptions = AsyncMock(return_value=[sub1, sub2])
    bus._create_and_dispatch_event = AsyncMock(side_effect=[first_event, second_event])

    event = await bus.emit(
        session,
        event_type="artifact.created",
        payload={"project_id": "project-1"},
    )

    assert event is first_event
    assert bus._create_and_dispatch_event.await_count == 2
