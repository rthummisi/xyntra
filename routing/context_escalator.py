from __future__ import annotations

from providers.capability_registry import ModelCapability


class ContextEscalator:
    def needs_escalation(
        self,
        *,
        estimated_tokens: int,
        candidate: ModelCapability,
    ) -> bool:
        return estimated_tokens > candidate.context_window


context_escalator = ContextEscalator()
