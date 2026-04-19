from __future__ import annotations

from providers.capability_registry import ModelCapability


def build_fallback_chain(candidates: list[ModelCapability]) -> list[ModelCapability]:
    return candidates[1:]
