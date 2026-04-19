from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.analytics import router as analytics_router
from core.database import get_db_session
from services.cost_service import cost_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(analytics_router, prefix="/api/v1")

    async def override_db():
        yield None

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_spend_summary_route_supports_grouping() -> None:
    app = build_test_app()
    original = cost_service.summarize_spend
    cost_service.summarize_spend = AsyncMock(
        return_value=[{"group": "gpt-4o-mini", "cost_usd": 1.25, "calls": 2}]
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/analytics/spend?group_by=model")

    cost_service.summarize_spend = original

    assert response.status_code == 200
    assert response.json()["items"][0]["group"] == "gpt-4o-mini"


async def test_spend_dashboard_route() -> None:
    app = build_test_app()
    original = cost_service.dashboard
    cost_service.dashboard = AsyncMock(
        return_value={
            "summary": {"total_cost_usd": 3.5, "total_calls": 4},
            "by_project": [],
            "by_model": [],
            "by_date": [],
        }
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/analytics/dashboard")

    cost_service.dashboard = original

    assert response.status_code == 200
    assert response.json()["summary"]["total_cost_usd"] == 3.5


async def test_quota_status_route() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/analytics/quota?consumed_tokens=85&token_quota=100"
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["threshold_reached"] is True
    assert payload["exceeded"] is False
