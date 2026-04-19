from providers.base.adapter import UnifiedMessage, UnifiedRequest
from providers.registry import provider_registry


async def test_provider_registry_contains_all_phase5_adapters() -> None:
    provider_names = {adapter.provider_name for adapter in provider_registry.list()}
    assert provider_names == {
        "anthropic",
        "deepseek",
        "gemini",
        "grok",
        "groq",
        "mistral",
        "ollama",
        "openai",
    }


async def test_openai_adapter_normalizes_request_shape() -> None:
    adapter = provider_registry.get("openai")
    request = UnifiedRequest(
        model="gpt-4o-mini",
        messages=[UnifiedMessage(role="user", content="ping")],
    )

    provider_request = adapter.normalize_request(request)

    assert provider_request.model == "gpt-4o-mini"
    assert provider_request.payload["messages"][0]["content"] == "ping"
