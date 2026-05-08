from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel


class ModelCapability(BaseModel):
    provider: str
    model: str
    context_window: int
    quality_tier: str
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_images: bool = False
    supports_pdf: bool = False
    local_only: bool = False
    cost_tier: str = "standard"
    latency_tier: str = "standard"


CapabilitySeed = tuple[str, int, str, dict]


def _opts(
    *,
    tools: bool = True,
    images: bool = False,
    pdf: bool = False,
    local: bool = False,
    streaming: bool = True,
    cost: str = "standard",
    latency: str = "standard",
) -> dict:
    return {
        "supports_tools": tools,
        "supports_images": images,
        "supports_pdf": pdf,
        "local_only": local,
        "supports_streaming": streaming,
        "cost_tier": cost,
        "latency_tier": latency,
    }


def _build_capabilities(
    provider: str,
    entries: Iterable[CapabilitySeed],
) -> list[ModelCapability]:
    return [
        ModelCapability(
            provider=provider,
            model=model,
            context_window=context_window,
            quality_tier=quality_tier,
            **options,
        )
        for model, context_window, quality_tier, options in entries
    ]


MM_PREMIUM = _opts(images=True, pdf=True, cost="premium")
MM_FAST = _opts(images=True, pdf=True, latency="fast")
IMG_FAST_ECON = _opts(images=True, cost="economy", latency="fast")
LOCAL_STD = _opts(local=True, cost="local", latency="local")
LOCAL_NOTOOLS = _opts(tools=False, local=True, cost="local", latency="local")
FAST_ECON = _opts(cost="economy", latency="fast")
LOCAL_EMBED = _opts(
    tools=False,
    local=True,
    streaming=False,
    cost="local",
    latency="local",
)


def _seed_capabilities() -> list[ModelCapability]:
    capabilities: list[ModelCapability] = []
    capabilities.extend(
        _build_capabilities(
            "anthropic",
            [
                ("claude-opus-4-7", 200_000, "premium", MM_PREMIUM),
                ("claude-sonnet-4-6", 200_000, "high", MM_PREMIUM),
                ("claude-haiku-4-5", 200_000, "medium", IMG_FAST_ECON),
                ("claude-3-5-sonnet-20241022", 200_000, "high", MM_PREMIUM),
                ("claude-3-5-haiku-20241022", 200_000, "medium", IMG_FAST_ECON),
                (
                    "claude-3-opus-20240229",
                    200_000,
                    "high",
                    _opts(images=True, cost="premium"),
                ),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "openai",
            [
                (
                    "gpt-4o",
                    128_000,
                    "high",
                    _opts(images=True, cost="premium", latency="fast"),
                ),
                ("gpt-4o-mini", 128_000, "medium", IMG_FAST_ECON),
                ("gpt-4-turbo", 128_000, "high", _opts(cost="premium")),
                ("gpt-4", 8_000, "medium", _opts(cost="premium")),
                ("gpt-3.5-turbo", 16_000, "economy", FAST_ECON),
                ("gpt-4.5", 128_000, "premium", _opts(images=True, cost="premium")),
                ("o1", 200_000, "premium", _opts(tools=False, cost="premium")),
                ("o1-mini", 128_000, "high", _opts(tools=False, latency="fast")),
                ("o1-pro", 200_000, "premium", _opts(tools=False, cost="premium")),
                ("o3", 200_000, "premium", _opts(cost="premium")),
                ("o3-mini", 200_000, "high", _opts(latency="fast")),
                ("o4-mini", 200_000, "high", _opts(images=True, latency="fast")),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "gemini",
            [
                ("gemini-2.5-pro", 1_000_000, "premium", MM_PREMIUM),
                ("gemini-2.0-flash", 1_000_000, "high", MM_FAST),
                ("gemini-2.0-flash-lite", 1_000_000, "medium", IMG_FAST_ECON),
                ("gemini-1.5-pro", 2_000_000, "premium", MM_PREMIUM),
                ("gemini-1.5-flash", 1_000_000, "medium", MM_FAST),
                ("gemini-1.0-pro", 32_000, "medium", _opts()),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "grok",
            [
                ("grok-3", 131_000, "premium", _opts(cost="premium")),
                ("grok-3-mini", 131_000, "high", _opts(latency="fast")),
                ("grok-2", 131_000, "high", _opts(cost="premium")),
                ("grok-2-mini", 131_000, "medium", FAST_ECON),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "mistral",
            [
                ("mistral-large-latest", 128_000, "high", _opts(cost="premium")),
                ("mistral-small-latest", 128_000, "medium", FAST_ECON),
                ("mistral-nemo", 128_000, "medium", _opts(latency="fast")),
                ("mixtral-8x7b", 32_000, "economy", _opts(cost="economy")),
                ("mixtral-8x22b", 64_000, "high", _opts()),
                ("codestral-latest", 32_000, "high", _opts(latency="fast")),
                ("pixtral-large", 128_000, "high", _opts(images=True, cost="premium")),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "deepseek",
            [
                ("deepseek-chat", 128_000, "high", _opts(latency="fast")),
                ("deepseek-reasoner", 128_000, "high", _opts(tools=False)),
                ("deepseek-r1:7b", 32_000, "local", LOCAL_STD),
                ("deepseek-r1:14b", 32_000, "local", LOCAL_STD),
                ("deepseek-r1:32b", 32_000, "local", LOCAL_STD),
                ("deepseek-r1:70b", 32_000, "local", LOCAL_STD),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "ollama",
            [
                ("llama3.3:70b", 128_000, "local", LOCAL_STD),
                ("llama3.2:90b", 128_000, "local", LOCAL_STD),
                ("llama3.2:11b", 128_000, "local", LOCAL_STD),
                ("llama3.2:3b", 128_000, "local", LOCAL_STD),
                ("llama3.2:1b", 128_000, "local", LOCAL_STD),
                ("llama3.1:405b", 128_000, "local", LOCAL_STD),
                ("llama3.1:70b", 128_000, "local", LOCAL_STD),
                ("llama3.1:8b", 128_000, "local", LOCAL_STD),
                ("llama3:70b", 8_000, "local", LOCAL_STD),
                ("llama3:8b", 8_000, "local", LOCAL_STD),
                ("codellama:70b", 16_000, "local", LOCAL_STD),
                ("codellama:34b", 16_000, "local", LOCAL_STD),
                ("qwen2.5:72b", 128_000, "local", LOCAL_STD),
                ("qwen2.5:32b", 128_000, "local", LOCAL_STD),
                ("qwen2.5:14b", 128_000, "local", LOCAL_STD),
                ("qwen2.5:7b", 128_000, "local", LOCAL_STD),
                ("qwen2.5-coder:32b", 128_000, "local", LOCAL_STD),
                ("qwen2.5-coder:7b", 128_000, "local", _opts(local=True, cost="local", latency="local", tools=True)),
                ("qwq:32b", 32_000, "local", LOCAL_NOTOOLS),
                ("phi4:14b", 16_000, "local", LOCAL_STD),
                ("phi3.5:3.8b", 128_000, "local", LOCAL_STD),
                ("phi3:14b", 128_000, "local", LOCAL_STD),
                ("gemma3:27b", 128_000, "local", LOCAL_STD),
                ("gemma3:12b", 128_000, "local", LOCAL_STD),
                ("gemma3:4b", 128_000, "local", LOCAL_STD),
                ("gemma3:1b", 32_000, "local", LOCAL_STD),
                ("gemma2:27b", 8_000, "local", LOCAL_STD),
                ("gemma2:9b", 8_000, "local", LOCAL_STD),
                ("gemma2:2b", 8_000, "local", LOCAL_STD),
                ("gemma:7b", 8_000, "local", LOCAL_STD),
                ("mistral", 32_000, "local", LOCAL_STD),
                ("nomic-embed-text", 8_192, "embedding", LOCAL_EMBED),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "groq",
            [
                ("llama-3.3-70b-versatile", 128_000, "high", _opts(latency="fast")),
                ("llama-3.1-8b-instant", 128_000, "medium", FAST_ECON),
                ("mixtral-8x7b-32768", 32_000, "economy", FAST_ECON),
                ("gemma2-9b-it", 8_000, "economy", FAST_ECON),
                (
                    "deepseek-r1-distill-llama-70b",
                    128_000,
                    "high",
                    _opts(tools=False, latency="fast"),
                ),
            ],
        )
    )
    return capabilities


class CapabilityRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelCapability] = {}
        for capability in _seed_capabilities():
            self._models[self._key(capability.provider, capability.model)] = capability

    def get(self, provider: str, model: str) -> ModelCapability | None:
        return self._models.get(self._key(provider, model))

    def list(self) -> list[ModelCapability]:
        return list(self._models.values())

    def by_provider(self, provider: str) -> list[ModelCapability]:
        return [
            capability
            for capability in self._models.values()
            if capability.provider == provider
        ]

    @staticmethod
    def _key(provider: str, model: str) -> str:
        return f"{provider}:{model}"


capability_registry = CapabilityRegistry()
