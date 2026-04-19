from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.router import router as routing_router
from providers.base.adapter import NormalizedResponse
from services.routing_service import RoutingDecision, routing_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routing_router, prefix="/api/v1")
    return app


async def test_router_api_returns_decision_and_response() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="ollama",
        selected_model="llama3.2:3b",
        classification={"request_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 1},
    )
    response_model = NormalizedResponse(
        provider="ollama",
        model="llama3.2:3b",
        content="hello",
        finish_reason="stop",
    )

    original = routing_service.route
    routing_service.route = AsyncMock(return_value=(decision, response_model))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/router",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["selected_provider"] == "ollama"
    assert payload["response"]["content"] == "hello"


async def test_router_api_returns_400_for_routing_error() -> None:
    app = build_test_app()
    original = routing_service.route
    routing_service.route = AsyncMock(side_effect=ValueError("PolicyViolation"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/router",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "bad"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 400
    assert response.json()["detail"] == "PolicyViolation"
