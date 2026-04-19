from __future__ import annotations

from types import MethodType

from providers.base.adapter import NormalizedRequest, UnifiedMessage, UnifiedRequest
from providers.ollama_adapter import OllamaAdapter


async def test_ollama_adapter_complete_stream_and_health() -> None:
    adapter = OllamaAdapter()
    request = UnifiedRequest(
        model="llama3.2:3b",
        messages=[UnifiedMessage(role="user", content="ping")],
    )
    normalized_request = NormalizedRequest(
        provider="ollama",
        request=adapter.normalize_request(request),
        unified=request,
    )

    async def fake_send_request(self, request, *, stream):
        return {
            "model": "llama3.2:3b",
            "response": "pong",
            "done": True,
            "usage": {"eval_count": 1},
        }

    adapter._send_request = MethodType(fake_send_request, adapter)

    response = await adapter.complete(normalized_request)
    chunks = [chunk async for chunk in adapter.stream(normalized_request)]
    health = await adapter.health_check()

    assert response.provider == "ollama"
    assert response.model == "llama3.2:3b"
    assert response.content == "pong"
    assert len(chunks) >= 1
    assert chunks[-1].finish_reason == "stop"
    assert health.provider == "ollama"
    assert health.status == "ok"
