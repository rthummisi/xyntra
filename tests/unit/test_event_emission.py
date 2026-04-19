from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from services.artifact_service import artifact_service
from services.session_service import session_service


async def test_create_artifact_emits_artifact_created_event() -> None:
    session = AsyncMock()
    session.add = Mock()
    project_id = uuid.uuid4()
    artifact = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=project_id,
        task_id=None,
        name="summary",
        kind="markdown",
        version=1,
        file_path="/tmp/summary.md",
    )

    original_versioning = artifact_service.create_artifact.__globals__[
        "artifact_versioning_service"
    ]
    original_event_bus = artifact_service.create_artifact.__globals__["event_bus"]
    mocked_event_bus = SimpleNamespace(emit=AsyncMock())
    artifact_service.create_artifact.__globals__["artifact_versioning_service"] = (
        SimpleNamespace(save_version=AsyncMock(return_value=artifact))
    )
    artifact_service.create_artifact.__globals__["event_bus"] = mocked_event_bus

    try:
        created = await artifact_service.create_artifact(
            session,
            project_id=project_id,
            task_id=None,
            name="summary",
            kind="markdown",
            content="# Summary",
        )
    finally:
        artifact_service.create_artifact.__globals__["artifact_versioning_service"] = (
            original_versioning
        )
        artifact_service.create_artifact.__globals__["event_bus"] = original_event_bus

    assert created is artifact
    mocked_event_bus.emit.assert_awaited_once()


async def test_branch_session_emits_session_branched_event() -> None:
    session = AsyncMock()
    session.add = Mock()
    source_session = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    branch_from_message_id = uuid.uuid4()
    branch_id = uuid.uuid4()
    source_message = SimpleNamespace(
        role="user",
        content="hello",
        sequence_number=1,
        attachments=[],
    )

    execute_result = Mock()
    execute_result.scalars.return_value.all.return_value = [source_message]
    session.execute.return_value = execute_result

    async def refresh_side_effect(branch):
        branch.id = branch_id

    session.refresh.side_effect = refresh_side_effect

    original_event_bus = session_service.branch_session.__globals__["event_bus"]
    mocked_event_bus = SimpleNamespace(emit=AsyncMock())
    session_service.branch_session.__globals__["event_bus"] = mocked_event_bus

    try:
        branch = await session_service.branch_session(
            session,
            source_session=source_session,
            branch_from_message_id=branch_from_message_id,
            title="Branch",
        )
    finally:
        session_service.branch_session.__globals__["event_bus"] = original_event_bus

    assert branch.title == "Branch"
    mocked_event_bus.emit.assert_awaited_once()
