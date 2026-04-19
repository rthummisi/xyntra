from __future__ import annotations

from context.semantic_cache import SemanticCache


async def test_semantic_cache_miss_then_hit(integration_redis) -> None:
    cache = SemanticCache(integration_redis)

    miss = await cache.get(
        normalized_prompt="hello world",
        model_family="ollama",
        system_prompt="system",
        local_only=False,
    )
    key = await cache.set(
        normalized_prompt="hello world",
        model_family="ollama",
        system_prompt="system",
        response="cached-response",
        local_only=True,
    )
    hit = await cache.get(
        normalized_prompt="hello world",
        model_family="ollama",
        system_prompt="system",
        local_only=True,
    )

    assert miss.hit is False
    assert hit.hit is True
    assert hit.key == key
    assert hit.value == "cached-response"
    assert hit.local_only is True


async def test_semantic_cache_rejects_hosted_entry_for_local_only(
    integration_redis,
) -> None:
    cache = SemanticCache(integration_redis)

    await cache.set(
        normalized_prompt="same prompt",
        model_family="openai",
        system_prompt="system",
        response="hosted-response",
        local_only=False,
    )
    hit = await cache.get(
        normalized_prompt="same prompt",
        model_family="openai",
        system_prompt="system",
        local_only=True,
    )

    assert hit.hit is False
