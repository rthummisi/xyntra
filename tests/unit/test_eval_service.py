from __future__ import annotations

from unittest.mock import AsyncMock

from providers.base.adapter import NormalizedResponse, UnifiedMessage
from providers.registry import provider_registry
from services.eval_service import EvalRequest, eval_service


async def test_eval_service_returns_ranked_results() -> None:
    request = EvalRequest(
        models=["gpt-4o-mini", "llama3.2:3b"],
        messages=[UnifiedMessage(role="user", content="ping")],
    )
    openai_adapter = provider_registry.get("openai")
    ollama_adapter = provider_registry.get("ollama")
    original_openai = openai_adapter.complete
    original_ollama = ollama_adapter.complete
    openai_adapter.complete = AsyncMock(
        return_value=NormalizedResponse(
            provider="openai",
            model="gpt-4o-mini",
            content="pong from openai",
            finish_reason="stop",
        )
    )
    ollama_adapter.complete = AsyncMock(
        return_value=NormalizedResponse(
            provider="ollama",
            model="llama3.2:3b",
            content="pong from ollama",
            finish_reason="stop",
        )
    )

    try:
        results = await eval_service.evaluate(request)
    finally:
        openai_adapter.complete = original_openai
        ollama_adapter.complete = original_ollama

    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert results[0].model
    assert results[0].reasoning
