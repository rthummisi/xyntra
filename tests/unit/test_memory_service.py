import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from services.memory_service import memory_service


async def test_memory_snapshot_aggregates_sources() -> None:
    session_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()

    original_session_messages = memory_service.snapshot.__globals__[
        "session_memory_store"
    ]
    original_summary_store = memory_service.snapshot.__globals__["summary_memory_store"]
    original_project_store = memory_service.snapshot.__globals__["project_memory_store"]
    original_preference_store = memory_service.snapshot.__globals__[
        "preference_memory_store"
    ]

    memory_service.snapshot.__globals__["session_memory_store"] = SimpleNamespace(
        fetch_messages=AsyncMock(
            return_value=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    role="user",
                    content="hello",
                    sequence_number=1,
                )
            ]
        )
    )
    memory_service.snapshot.__globals__["summary_memory_store"] = SimpleNamespace(
        list_summaries=AsyncMock(
            return_value=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    summary_type="summary",
                    content="brief",
                    token_count=12,
                )
            ]
        )
    )
    memory_service.snapshot.__globals__["project_memory_store"] = SimpleNamespace(
        fetch_project_state=AsyncMock(
            return_value=SimpleNamespace(state={"branch": "main"})
        ),
        list_decisions=AsyncMock(
            return_value=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    decision_type="router",
                    summary="picked local model",
                )
            ]
        ),
    )
    memory_service.snapshot.__globals__["preference_memory_store"] = SimpleNamespace(
        list_user_preferences=AsyncMock(
            return_value=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    name="default",
                    version=1,
                    tags=["code"],
                )
            ]
        )
    )

    snapshot = await memory_service.snapshot(
        None,
        session_id=session_id,
        project_id=project_id,
        user_id=user_id,
    )

    memory_service.snapshot.__globals__["session_memory_store"] = (
        original_session_messages
    )
    memory_service.snapshot.__globals__["summary_memory_store"] = original_summary_store
    memory_service.snapshot.__globals__["project_memory_store"] = original_project_store
    memory_service.snapshot.__globals__["preference_memory_store"] = (
        original_preference_store
    )

    assert snapshot.project_state == {"branch": "main"}
    assert snapshot.session_messages[0]["content"] == "hello"
    assert snapshot.user_preferences[0]["tags"] == ["code"]
