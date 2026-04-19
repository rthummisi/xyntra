from __future__ import annotations

from providers.anthropic_adapter import AnthropicAdapter
from providers.base.adapter import BaseAdapter
from providers.deepseek_adapter import DeepSeekAdapter
from providers.gemini_adapter import GeminiAdapter
from providers.grok_adapter import GrokAdapter
from providers.groq_adapter import GroqAdapter
from providers.mistral_adapter import MistralAdapter
from providers.ollama_adapter import OllamaAdapter
from providers.openai_adapter import OpenAIAdapter


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseAdapter] = {
            "anthropic": AnthropicAdapter(),
            "openai": OpenAIAdapter(),
            "ollama": OllamaAdapter(),
            "gemini": GeminiAdapter(),
            "grok": GrokAdapter(),
            "mistral": MistralAdapter(),
            "deepseek": DeepSeekAdapter(),
            "groq": GroqAdapter(),
        }

    def get(self, provider_name: str) -> BaseAdapter:
        return self._providers[provider_name]

    def list(self) -> list[BaseAdapter]:
        return list(self._providers.values())


provider_registry = ProviderRegistry()
