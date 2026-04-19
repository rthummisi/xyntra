from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.replay import router as replay_router
from core.database import get_db_session
from services.replay_service import replay_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(replay_router, prefix="/api/v1")

    async def override_db():
        yield None

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_replay_route_returns_payload() -> None:
    app = build_test_app()
    task_run_id = uuid.uuid4()
    original = replay_service.replay_task_run
    replay_service.replay_task_run = AsyncMock(
        return_value={
            "task": {"id": "1", "name": "test"},
            "task_run": {"id": str(task_run_id), "status": "completed"},
            "provider_calls": [],
            "telemetry": [],
        }
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/api/v1/replay/{task_run_id}")

    replay_service.replay_task_run = original

    assert response.status_code == 200
    assert response.json()["payload"]["task_run"]["status"] == "completed"


async def test_replay_route_returns_404_for_missing_task_run() -> None:
    app = build_test_app()
    task_run_id = uuid.uuid4()
    original = replay_service.replay_task_run
    replay_service.replay_task_run = AsyncMock(
        side_effect=ValueError("Task run not found.")
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/api/v1/replay/{task_run_id}")

    replay_service.replay_task_run = original

    assert response.status_code == 404
    assert response.json()["detail"] == "Task run not found."
