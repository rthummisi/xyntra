from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.evals import router as evals_router
from providers.base.adapter import NormalizedResponse
from services.eval_service import EvalResult, eval_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(evals_router, prefix="/api/v1")
    return app


async def test_run_eval_route() -> None:
    app = build_test_app()
    original = eval_service.evaluate
    eval_service.evaluate = AsyncMock(
        return_value=[
            EvalResult(
                provider="openai",
                model="gpt-4o-mini",
                score=0.9,
                reasoning="best",
                response=NormalizedResponse(
                    provider="openai",
                    model="gpt-4o-mini",
                    content="pong",
                    finish_reason="stop",
                ),
            ),
            EvalResult(
                provider="ollama",
                model="llama3.2:3b",
                score=0.7,
                reasoning="second",
                response=NormalizedResponse(
                    provider="ollama",
                    model="llama3.2:3b",
                    content="pong",
                    finish_reason="stop",
                ),
            ),
        ]
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/evals",
                json={
                    "models": ["gpt-4o-mini", "llama3.2:3b"],
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
    finally:
        eval_service.evaluate = original

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 2
    assert "score" in payload["results"][0]


async def test_run_eval_route_returns_404_for_unknown_model() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/evals",
            json={
                "models": ["missing-model"],
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    assert response.status_code == 404
    assert "Model not found" in response.json()["detail"]
