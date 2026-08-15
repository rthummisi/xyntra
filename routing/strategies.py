from __future__ import annotations

from providers.capability_registry import ModelCapability
from routing.classifier import RoutingClassification


class RoutingStrategySelector:
    def apply(
        self,
        classification: RoutingClassification,
        candidates: list[ModelCapability],
        *,
        strategy: str | None = None,
    ) -> list[ModelCapability]:
        # Priority is always the primary sort key (higher = preferred first).
        # Inkling=100, Nemotron=90, Qwen=70 sit above cloud giants=50, so they
        # win the top slot before secondary criteria are applied.
        selected_strategy = strategy or classification.preferred_strategy
        if selected_strategy == "latency":
            return sorted(candidates, key=lambda item: (-item.priority, item.latency_tier))
        if selected_strategy == "cost":
            return sorted(candidates, key=lambda item: (-item.priority, item.cost_tier))
        if selected_strategy == "quality":
            return sorted(candidates, key=lambda item: (-item.priority, item.quality_tier))
        return sorted(candidates, key=lambda item: (-item.priority, item.cost_tier, item.latency_tier))


strategy_selector = RoutingStrategySelector()
