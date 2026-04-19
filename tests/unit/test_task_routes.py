from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.tasks import router as tasks_router
from core.database import get_db_session
from services.task_service import task_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1")

    async def override_db():
        yield None

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_dlq_entry_routes() -> None:
    app = build_test_app()
    entry_id = uuid.uuid4()
    entry = SimpleNamespace(
        id=entry_id,
        task_name="broken-task",
        payload={"step": 1},
        error_history=[{"error": "boom"}],
        retry_count=0,
        status="failed",
        last_error="boom",
    )

    original_get = task_service.get_dlq_entry
    original_retry = task_service.retry_dlq_entry
    original_discard = task_service.discard_dlq_entry
    task_service.get_dlq_entry = AsyncMock(return_value=entry)
    task_service.retry_dlq_entry = AsyncMock(
        return_value=SimpleNamespace(
            **{**entry.__dict__, "retry_count": 1, "status": "requeued"}
        )
    )
    task_service.discard_dlq_entry = AsyncMock(
        return_value=SimpleNamespace(**{**entry.__dict__, "status": "discarded"})
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        get_response = await client.get(f"/api/v1/tasks/dlq/{entry_id}")
        retry_response = await client.post(f"/api/v1/tasks/dlq/{entry_id}/retry")
        discard_response = await client.post(f"/api/v1/tasks/dlq/{entry_id}/discard")

    task_service.get_dlq_entry = original_get
    task_service.retry_dlq_entry = original_retry
    task_service.discard_dlq_entry = original_discard

    assert get_response.status_code == 200
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == "requeued"
    assert discard_response.status_code == 200
    assert discard_response.json()["status"] == "discarded"
