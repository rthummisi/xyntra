from __future__ import annotations

from pydantic import BaseModel

from providers.base.adapter import UnifiedRequest


class RoutingClassification(BaseModel):
    task_type: str
    requires_multimodal: bool
    requires_tools: bool
    preferred_strategy: str


class RoutingClassifier:
    def classify(self, request: UnifiedRequest) -> RoutingClassification:
        requires_multimodal = bool(request.attachments)
        requires_tools = bool(request.tools)
        task_type = "chat"
        if requires_tools:
            task_type = "tool_use"
        elif requires_multimodal:
            task_type = "multimodal"
        return RoutingClassification(
            task_type=task_type,
            requires_multimodal=requires_multimodal,
            requires_tools=requires_tools,
            preferred_strategy="balanced",
        )


routing_classifier = RoutingClassifier()
