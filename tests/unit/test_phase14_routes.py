from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.chat import router as chat_router
from api.v1.compare import router as compare_router
from api.v1.openai_compat import router as openai_compat_router
from api.v1.providers import router as providers_router
from providers.base.adapter import NormalizedResponse, StreamChunk
from providers.registry import provider_registry
from services.routing_service import RoutingDecision, routing_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(compare_router, prefix="/api/v1")
    app.include_router(providers_router, prefix="/api/v1")
    app.include_router(openai_compat_router)
    return app


async def test_chat_completion_route() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="ollama",
        selected_model="llama3.2:3b",
        classification={"request_type": "chat"},
        fallback_chain=["ollama:qwen2.5:7b"],
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
            "/api/v1/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "hello"}],
                "local_only": True,
            },
        )

    routing_service.route = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["selected_provider"] == "ollama"
    assert payload["response"]["content"] == "hello"


async def test_chat_stream_route() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="ollama",
        selected_model="llama3.2:3b",
        classification={"request_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 1},
    )

    async def fake_stream():
        yield StreamChunk(delta="hel")
        yield StreamChunk(delta="lo", finish_reason="stop")

    original = routing_service.stream_route
    routing_service.stream_route = Mock(return_value=(decision, fake_stream()))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "hello"}],
                "local_only": True,
                "stream": True,
            },
        )

    routing_service.stream_route = original

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: decision" in response.text
    assert "event: chunk" in response.text
    assert '"delta": "hel"' in response.text
    assert "event: done" in response.text


async def test_chat_completion_route_returns_400_for_routing_error() -> None:
    app = build_test_app()
    original = routing_service.route
    routing_service.route = AsyncMock(side_effect=ValueError("QuotaExceeded"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 400
    assert response.json()["detail"] == "QuotaExceeded"


async def test_list_providers_route() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/providers")

    assert response.status_code == 200
    providers = {entry["provider"]: entry for entry in response.json()}
    assert "openai" in providers
    assert "ollama" in providers
    assert providers["ollama"]["local_only"] is True


async def test_provider_health_route() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/providers/health")

    assert response.status_code == 200
    payload = response.json()
    assert any(entry["provider"] == "openai" for entry in payload)
    assert any(entry["provider"] == "ollama" for entry in payload)
    assert any("target" in entry["details"] for entry in payload)


async def test_provider_capabilities_route_filters_by_provider() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/providers/capabilities?provider=ollama")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(entry["provider"] == "ollama" for entry in payload)


async def test_provider_leaderboard_route() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/providers/leaderboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert "provider" in payload[0]
    assert "model" in payload[0]


async def test_compare_route() -> None:
    app = build_test_app()
    original_openai = provider_registry.get("openai").complete
    original_ollama = provider_registry.get("ollama").complete
    provider_registry.get("openai").complete = AsyncMock(
        return_value=NormalizedResponse(
            provider="openai",
            model="gpt-4o-mini",
            content="hello",
            finish_reason="stop",
        )
    )
    provider_registry.get("ollama").complete = AsyncMock(
        return_value=NormalizedResponse(
            provider="ollama",
            model="llama3.2:3b",
            content="hello",
            finish_reason="stop",
        )
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/compare",
                json={
                    "models": ["gpt-4o-mini", "llama3.2:3b"],
                    "messages": [{"role": "user", "content": "hello"}],
                },
            )
    finally:
        provider_registry.get("openai").complete = original_openai
        provider_registry.get("ollama").complete = original_ollama

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 2
    assert {result["provider"] for result in payload["results"]} == {
        "openai",
        "ollama",
    }


async def test_compare_route_returns_404_for_unknown_model() -> None:
    app = build_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/compare",
            json={
                "models": ["missing-model", "gpt-4o-mini"],
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

    assert response.status_code == 404
    assert "Model not found" in response.json()["detail"]


async def test_openai_compat_completion_route() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="openai",
        selected_model="gpt-4o-mini",
        classification={"request_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 2},
    )
    response_model = NormalizedResponse(
        provider="openai",
        model="gpt-4o-mini",
        content="pong",
        finish_reason="stop",
        usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    )

    original = routing_service.route
    routing_service.route = AsyncMock(return_value=(decision, response_model))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["choices"][0]["message"]["content"] == "pong"
    assert payload["usage"]["total_tokens"] == 2


async def test_openai_compat_completion_route_maps_alias_model() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="openai",
        selected_model="gpt-4o-mini",
        classification={"request_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 2},
    )
    response_model = NormalizedResponse(
        provider="openai",
        model="gpt-4o-mini",
        content="pong",
        finish_reason="stop",
        usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    )

    original = routing_service.route
    routing_service.route = AsyncMock(return_value=(decision, response_model))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "gpt-4.1-mini"


async def test_openai_compat_stream_route() -> None:
    app = build_test_app()
    decision = RoutingDecision(
        selected_provider="openai",
        selected_model="gpt-4o-mini",
        classification={"request_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 1},
    )

    async def fake_stream():
        yield StreamChunk(delta="po")
        yield StreamChunk(delta="ng", finish_reason="stop")

    original = routing_service.stream_route
    routing_service.stream_route = Mock(return_value=(decision, fake_stream()))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "ping"}],
                "stream": True,
            },
        )

    routing_service.stream_route = original

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"object": "chat.completion.chunk"' in response.text
    assert '"content": "po"' in response.text
    assert "data: [DONE]" in response.text


async def test_openai_compat_route_returns_400_for_routing_error() -> None:
    app = build_test_app()
    original = routing_service.route
    routing_service.route = AsyncMock(side_effect=ValueError("PolicyViolation"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    routing_service.route = original

    assert response.status_code == 400
    assert response.json()["detail"] == "PolicyViolation"
