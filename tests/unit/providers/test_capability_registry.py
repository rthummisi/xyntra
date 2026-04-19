from __future__ import annotations

from providers.capability_registry import capability_registry


def test_capability_registry_has_broad_model_coverage() -> None:
    models = capability_registry.list()

    assert len(models) >= 50
    assert capability_registry.get("openai", "gpt-4o") is not None
    assert capability_registry.get("anthropic", "claude-sonnet-4-6") is not None
    assert capability_registry.get("gemini", "gemini-2.5-pro") is not None
    assert capability_registry.get("ollama", "llama3.2:3b") is not None


def test_capability_registry_marks_local_models_correctly() -> None:
    local_model = capability_registry.get("ollama", "qwen2.5:7b")
    remote_model = capability_registry.get("openai", "gpt-4o")

    assert local_model is not None
    assert local_model.local_only is True
    assert local_model.cost_tier == "local"
    assert remote_model is not None
    assert remote_model.local_only is False
