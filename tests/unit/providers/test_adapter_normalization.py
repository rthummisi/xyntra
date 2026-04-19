from __future__ import annotations

from types import MethodType

from providers.anthropic_adapter import AnthropicAdapter
from providers.base.adapter import (
    NormalizedRequest,
    ToolCall,
    UnifiedMessage,
    UnifiedRequest,
)
from providers.deepseek_adapter import DeepSeekAdapter
from providers.gemini_adapter import GeminiAdapter
from providers.grok_adapter import GrokAdapter
from providers.groq_adapter import GroqAdapter
from providers.mistral_adapter import MistralAdapter
from providers.ollama_adapter import OllamaAdapter
from providers.openai_adapter import OpenAIAdapter


def _build_request(model: str) -> UnifiedRequest:
    return UnifiedRequest(
        model=model,
        messages=[UnifiedMessage(role="user", content="ping")],
        system_prompt="system",
        tools=[ToolCall(name="search", arguments={"query": "ping"})],
        attachments=[
            {
                "kind": "image",
                "media_type": "image/png",
                "content": "base64-data",
            }
        ],
        metadata={"request_id": "req-1"},
    )


async def test_openai_family_adapters_normalize_openai_shape() -> None:
    for adapter in [
        OpenAIAdapter(),
        GrokAdapter(),
        GroqAdapter(),
        MistralAdapter(),
        DeepSeekAdapter(),
    ]:
        request = _build_request(model=f"{adapter.provider_name}-model")
        provider_request = adapter.normalize_request(request)

        assert provider_request.payload["messages"][0]["role"] == "system"
        assert provider_request.payload["messages"][1]["content"] == "ping"
        assert provider_request.payload["tools"][0]["function"]["name"] == "search"
        assert provider_request.payload["attachments"][0]["media_type"] == "image/png"


async def test_anthropic_adapter_normalizes_messages_to_content_blocks() -> None:
    adapter = AnthropicAdapter()
    request = _build_request(model="claude-sonnet-4-6")

    provider_request = adapter.normalize_request(request)
    response = adapter.normalize_response(
        {
            "model": "claude-sonnet-4-6",
            "content": [{"type": "text", "text": "pong"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 2, "output_tokens": 1},
        }
    )

    assert provider_request.payload["system"] == "system"
    assert provider_request.payload["max_tokens"] == 1024
    assert provider_request.payload["messages"][0]["content"][0]["text"] == "ping"
    assert provider_request.payload["tools"][0]["input_schema"]["query"] == "ping"
    assert response.content == "pong"
    assert response.finish_reason == "end_turn"


async def test_gemini_adapter_normalizes_contents_and_candidates() -> None:
    adapter = GeminiAdapter()
    request = _build_request(model="gemini-2.5-pro")

    provider_request = adapter.normalize_request(request)
    response = adapter.normalize_response(
        {
            "model": "gemini-2.5-pro",
            "candidates": [
                {
                    "content": {"parts": [{"text": "pong"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"promptTokenCount": 2},
        }
    )

    assert provider_request.payload["contents"][0]["parts"][0]["text"] == "system"
    assert provider_request.payload["contents"][1]["parts"][0]["text"] == "ping"
    assert (
        provider_request.payload["tools"][0]["functionDeclarations"][0]["name"]
        == "search"
    )
    assert response.content == "pong"
    assert response.finish_reason == "STOP"


async def test_ollama_adapter_normalizes_prompt_and_images() -> None:
    adapter = OllamaAdapter()
    request = _build_request(model="llama3.2:3b")

    provider_request = adapter.normalize_request(request)
    response = adapter.normalize_response(
        {
            "model": "llama3.2:3b",
            "message": {"content": "pong"},
            "done": True,
            "usage": {"eval_count": 1},
        }
    )

    assert "system" in provider_request.payload["prompt"]
    assert "ping" in provider_request.payload["prompt"]
    assert provider_request.payload["images"] == ["base64-data"]
    assert response.content == "pong"
    assert response.finish_reason == "stop"


async def test_adapter_complete_and_stream_use_mocked_transport() -> None:
    adapter = OpenAIAdapter()
    request = _build_request(model="gpt-4o")
    normalized_request = NormalizedRequest(
        provider="openai",
        request=adapter.normalize_request(request),
        unified=request,
    )

    async def fake_send_request(self, request, *, stream):
        return {
            "model": "gpt-4o",
            "choices": [
                {
                    "message": {"content": "pong"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 3,
            },
        }

    adapter._send_request = MethodType(fake_send_request, adapter)

    response = await adapter.complete(normalized_request)
    chunks = [chunk async for chunk in adapter.stream(normalized_request)]
    health = await adapter.health_check()

    assert response.content == "pong"
    assert response.finish_reason == "stop"
    assert chunks[0].delta == "pong"
    assert chunks[-1].finish_reason == "stop"
    assert health.provider == "openai"
    assert health.status == "degraded"
    assert health.details["target"] == "OPENAI_API_KEY"
