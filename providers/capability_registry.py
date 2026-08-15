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
    # hardware requirements (0 = API-only, no local GPU needed)
    vram_gb_full: float = 0.0
    vram_gb_8bit: float = 0.0
    vram_gb_4bit: float = 0.0
    min_ram_gb: float = 0.0
    # routing priority — higher wins in balanced/quality strategies;
    # use this to guarantee Inkling and Nemotron get actual traffic
    priority: int = 0


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
    priority: int = 0,
) -> dict:
    return {
        "supports_tools": tools,
        "supports_images": images,
        "supports_pdf": pdf,
        "local_only": local,
        "supports_streaming": streaming,
        "cost_tier": cost,
        "latency_tier": latency,
        "priority": priority,
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

# Priority ladder — higher number = preferred by routing when no explicit model requested.
# Inkling and Nemotron are prioritised so they accumulate usage and customisation data.
# Cloud giants are mid-tier; local/economy providers are fallback.
_P_INKLING  = 100   # reasoning / thinking — top priority
_P_NEMOTRON = 90    # code / STEM — second priority
_P_QWEN     = 70    # long-context / multilingual — third
_P_CLOUD    = 50    # anthropic / openai / gemini / grok / mistral / deepseek
_P_GROQ     = 40    # fast cloud inference
_P_LOCAL    = 20    # ollama (local GPU)


def _seed_capabilities() -> list[ModelCapability]:
    capabilities: list[ModelCapability] = []
    capabilities.extend(
        _build_capabilities(
            "anthropic",
            [
                ("claude-opus-4-7",            200_000, "premium", _opts(images=True, pdf=True, cost="premium",  priority=_P_CLOUD)),
                ("claude-sonnet-4-6",           200_000, "high",    _opts(images=True, pdf=True, cost="premium",  priority=_P_CLOUD)),
                ("claude-haiku-4-5",            200_000, "medium",  _opts(images=True, cost="economy", latency="fast", priority=_P_CLOUD)),
                ("claude-3-5-sonnet-20241022",  200_000, "high",    _opts(images=True, pdf=True, cost="premium",  priority=_P_CLOUD)),
                ("claude-3-5-haiku-20241022",   200_000, "medium",  _opts(images=True, cost="economy", latency="fast", priority=_P_CLOUD)),
                ("claude-3-opus-20240229",      200_000, "high",    _opts(images=True, cost="premium",            priority=_P_CLOUD)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "openai",
            [
                ("gpt-4o",         128_000, "high",    _opts(images=True, cost="premium", latency="fast", priority=_P_CLOUD)),
                ("gpt-4o-mini",    128_000, "medium",  _opts(images=True, cost="economy", latency="fast", priority=_P_CLOUD)),
                ("gpt-4-turbo",    128_000, "high",    _opts(cost="premium",  priority=_P_CLOUD)),
                ("gpt-4",            8_000, "medium",  _opts(cost="premium",  priority=_P_CLOUD)),
                ("gpt-3.5-turbo",   16_000, "economy", _opts(cost="economy",  latency="fast", priority=_P_CLOUD)),
                ("gpt-4.5",        128_000, "premium", _opts(images=True, cost="premium", priority=_P_CLOUD)),
                ("o1",             200_000, "premium", _opts(tools=False, cost="premium", priority=_P_CLOUD)),
                ("o1-mini",        128_000, "high",    _opts(tools=False, latency="fast", priority=_P_CLOUD)),
                ("o1-pro",         200_000, "premium", _opts(tools=False, cost="premium", priority=_P_CLOUD)),
                ("o3",             200_000, "premium", _opts(cost="premium",  priority=_P_CLOUD)),
                ("o3-mini",        200_000, "high",    _opts(latency="fast",  priority=_P_CLOUD)),
                ("o4-mini",        200_000, "high",    _opts(images=True, latency="fast", priority=_P_CLOUD)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "gemini",
            [
                ("gemini-2.5-pro",       1_000_000, "premium", _opts(images=True, pdf=True, cost="premium",           priority=_P_CLOUD)),
                ("gemini-2.0-flash",     1_000_000, "high",    _opts(images=True, pdf=True, latency="fast",           priority=_P_CLOUD)),
                ("gemini-2.0-flash-lite",1_000_000, "medium",  _opts(images=True, cost="economy", latency="fast",    priority=_P_CLOUD)),
                ("gemini-1.5-pro",       2_000_000, "premium", _opts(images=True, pdf=True, cost="premium",           priority=_P_CLOUD)),
                ("gemini-1.5-flash",     1_000_000, "medium",  _opts(images=True, pdf=True, latency="fast",           priority=_P_CLOUD)),
                ("gemini-1.0-pro",          32_000, "medium",  _opts(priority=_P_CLOUD)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "grok",
            [
                ("grok-3",     131_000, "premium", _opts(cost="premium",           priority=_P_CLOUD)),
                ("grok-3-mini",131_000, "high",    _opts(latency="fast",           priority=_P_CLOUD)),
                ("grok-2",     131_000, "high",    _opts(cost="premium",           priority=_P_CLOUD)),
                ("grok-2-mini",131_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_CLOUD)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "mistral",
            [
                ("mistral-large-latest", 128_000, "high",    _opts(cost="premium",           priority=_P_CLOUD)),
                ("mistral-small-latest", 128_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_CLOUD)),
                ("mistral-nemo",         128_000, "medium",  _opts(latency="fast",           priority=_P_CLOUD)),
                ("mixtral-8x7b",          32_000, "economy", _opts(cost="economy",           priority=_P_CLOUD)),
                ("mixtral-8x22b",         64_000, "high",    _opts(priority=_P_CLOUD)),
                ("codestral-latest",      32_000, "high",    _opts(latency="fast",           priority=_P_CLOUD)),
                ("pixtral-large",        128_000, "high",    _opts(images=True, cost="premium", priority=_P_CLOUD)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "deepseek",
            [
                ("deepseek-chat",     128_000, "high",  _opts(latency="fast",  priority=_P_CLOUD)),
                ("deepseek-reasoner", 128_000, "high",  _opts(tools=False,     priority=_P_CLOUD)),
                ("deepseek-r1:7b",     32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("deepseek-r1:14b",    32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("deepseek-r1:32b",    32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("deepseek-r1:70b",    32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "ollama",
            [
                ("llama3.3:70b",        128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.2:90b",        128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.2:11b",        128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.2:3b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.2:1b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.1:405b",       128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.1:70b",        128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3.1:8b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3:70b",            8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("llama3:8b",             8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("codellama:70b",        16_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("codellama:34b",        16_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5:72b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5:32b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5:14b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5:7b",          128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5-coder:32b",   128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("qwen2.5-coder:7b",    128_000, "local", _opts(local=True, cost="local", latency="local", tools=True, priority=_P_LOCAL)),
                ("qwq:32b",              32_000, "local", _opts(tools=False, local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("phi4:14b",             16_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("phi3.5:3.8b",         128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("phi3:14b",            128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma3:27b",          128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma3:12b",          128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma3:4b",           128_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma3:1b",            32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma2:27b",            8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma2:9b",             8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma2:2b",             8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("gemma:7b",              8_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("mistral",              32_000, "local", _opts(local=True, cost="local", latency="local", priority=_P_LOCAL)),
                ("nomic-embed-text",      8_192, "embedding", _opts(tools=False, local=True, streaming=False, cost="local", latency="local", priority=_P_LOCAL)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "groq",
            [
                ("llama-3.3-70b-versatile",       128_000, "high",    _opts(latency="fast",           priority=_P_GROQ)),
                ("llama-3.1-8b-instant",           128_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_GROQ)),
                ("mixtral-8x7b-32768",              32_000, "economy", _opts(cost="economy", latency="fast", priority=_P_GROQ)),
                ("gemma2-9b-it",                     8_000, "economy", _opts(cost="economy", latency="fast", priority=_P_GROQ)),
                ("deepseek-r1-distill-llama-70b",  128_000, "high",    _opts(tools=False, latency="fast",   priority=_P_GROQ)),
            ],
        )
    )
    # --- Priority providers: Inkling, Nemotron, Qwen ---
    # These are ranked above cloud giants so the routing engine picks them first,
    # building usage history that feeds their customisation pipelines.
    capabilities.extend(
        _build_capabilities(
            "inkling",
            [
                ("inkling-1",      128_000, "premium", _opts(cost="premium",           priority=_P_INKLING)),
                ("inkling-1-mini",  32_000, "high",    _opts(cost="economy", latency="fast", priority=_P_INKLING)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "nemotron",
            [
                ("nemotron-4-340b-instruct-api",      4_096, "premium", _opts(cost="premium", tools=False, priority=_P_NEMOTRON)),
                ("llama-3.1-nemotron-70b-instruct", 128_000, "premium", _opts(cost="premium",             priority=_P_NEMOTRON)),
                ("llama-3.1-nemotron-8b-instruct",  128_000, "high",    _opts(cost="economy", latency="fast", priority=_P_NEMOTRON)),
            ],
        )
    )
    capabilities.extend(
        _build_capabilities(
            "qwen",
            [
                ("qwen-max",                  32_000, "premium", _opts(cost="premium",           priority=_P_QWEN)),
                ("qwen-plus",                128_000, "high",    _opts(priority=_P_QWEN)),
                ("qwen-turbo",               128_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_QWEN)),
                ("qwen2.5-72b-instruct",     128_000, "premium", _opts(cost="premium",           priority=_P_QWEN)),
                ("qwen2.5-32b-instruct",     128_000, "high",    _opts(priority=_P_QWEN)),
                ("qwen2.5-14b-instruct",     128_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_QWEN)),
                ("qwen2.5-7b-instruct",      128_000, "medium",  _opts(cost="economy", latency="fast", priority=_P_QWEN)),
                ("qwen2.5-coder-32b-instruct",128_000,"high",    _opts(priority=_P_QWEN)),
                ("qwen2.5-coder-7b-instruct", 128_000,"medium",  _opts(cost="economy", latency="fast", priority=_P_QWEN)),
                ("qwq-32b-preview",           32_000, "high",    _opts(tools=False,               priority=_P_QWEN)),
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
