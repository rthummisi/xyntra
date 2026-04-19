from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.events import router as events_router
from api.v1.webhooks import router as webhooks_router
from core.database import get_db_session
from core.events import event_bus
from models.webhook import WebhookSubscription


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(webhooks_router, prefix="/api/v1")
    app.include_router(events_router, prefix="/api/v1")

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_list_events_route() -> None:
    app = build_test_app()
    event = SimpleNamespace(
        id=uuid.uuid4(),
        subscription_id=None,
        event_type="task.completed",
        payload={"project_id": "123"},
        delivery_status="pending",
        attempt_count=0,
        error_message=None,
    )
    original = event_bus.list_events
    event_bus.list_events = AsyncMock(return_value=[event])

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/events?event_type=task.completed")

    event_bus.list_events = original

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "task.completed"


async def test_create_and_list_webhook_subscriptions() -> None:
    app = build_test_app()
    db = AsyncMock()
    created = WebhookSubscription(
        project_id=None,
        target_url="https://example.com/hook",
        secret="secret",
        event_types=["task.completed"],
        is_active=True,
    )
    created.id = uuid.uuid4()

    async def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db

    async def refresh_side_effect(model):
        model.id = created.id

    db.add = Mock()
    db.refresh.side_effect = refresh_side_effect
    execute_result = Mock()
    execute_result.scalars.return_value.all.return_value = [created]
    db.execute.return_value = execute_result

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/webhooks",
            json={
                "target_url": "https://example.com/hook",
                "secret": "secret",
                "event_types": ["task.completed"],
                "is_active": True,
            },
        )
        list_response = await client.get("/api/v1/webhooks")

    assert create_response.status_code == 201
    assert create_response.json()["target_url"] == "https://example.com/hook"
    assert list_response.status_code == 200
    assert list_response.json()[0]["event_types"] == ["task.completed"]


async def test_get_update_and_delete_webhook_subscription() -> None:
    app = build_test_app()
    subscription_id = uuid.uuid4()
    db = AsyncMock()
    subscription = WebhookSubscription(
        project_id=None,
        target_url="https://example.com/original",
        secret="secret",
        event_types=["task.completed"],
        is_active=True,
    )
    subscription.id = subscription_id

    async def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
    db.get.return_value = subscription

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        get_response = await client.get(f"/api/v1/webhooks/{subscription_id}")
        patch_response = await client.patch(
            f"/api/v1/webhooks/{subscription_id}",
            json={"target_url": "https://example.com/updated", "is_active": False},
        )
        delete_response = await client.delete(f"/api/v1/webhooks/{subscription_id}")

    assert get_response.status_code == 200
    assert patch_response.status_code == 200
    assert patch_response.json()["target_url"] == "https://example.com/updated"
    assert patch_response.json()["is_active"] is False
    assert delete_response.status_code == 204
