from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from providers.base.adapter import NormalizedResponse, StreamChunk
from services.routing_service import RoutingDecision, routing_service


def _decision() -> RoutingDecision:
    return RoutingDecision(
        selected_provider="openai",
        selected_model="gpt-4o-mini",
        classification={"task_type": "chat"},
        fallback_chain=[],
        metadata={"estimated_tokens": 1},
    )


async def test_openai_compat_chat_completion(e2e_client) -> None:
    original = routing_service.route
    routing_service.route = AsyncMock(
        return_value=(
            _decision(),
            NormalizedResponse(
                provider="openai",
                model="gpt-4o-mini",
                content="pong",
                finish_reason="stop",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            ),
        )
    )

    try:
        response = await e2e_client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "ping"}],
            },
        )
    finally:
        routing_service.route = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert payload["model"]


async def test_openai_compat_streaming(e2e_client) -> None:
    async def fake_stream():
        yield StreamChunk(delta="pong")
        yield StreamChunk(delta="", finish_reason="stop")

    original = routing_service.stream_route
    routing_service.stream_route = Mock(return_value=(_decision(), fake_stream()))

    try:
        response = await e2e_client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "ping"}],
                "stream": True,
            },
        )
    finally:
        routing_service.stream_route = original

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"object": "chat.completion.chunk"' in response.text
    assert "data: [DONE]" in response.text


async def test_openai_python_client_compatibility(e2e_client) -> None:
    openai = pytest.importorskip("openai")
    original = routing_service.route
    routing_service.route = AsyncMock(
        return_value=(
            _decision(),
            NormalizedResponse(
                provider="openai",
                model="gpt-4o-mini",
                content="pong",
                finish_reason="stop",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            ),
        )
    )

    try:
        client = openai.AsyncOpenAI(
            api_key="test-key",
            base_url="http://test/v1",
            http_client=e2e_client,
        )
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
        )
    finally:
        routing_service.route = original

    assert response.object == "chat.completion"
    assert response.choices[0].message.role == "assistant"
