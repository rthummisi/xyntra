from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    ToolCall,
    UnifiedMessage,
    UnifiedRequest,
)
from providers.capability_registry import ModelCapability, capability_registry
from providers.registry import provider_registry


class EvalRequest(BaseModel):
    models: list[str] = Field(min_length=1)
    messages: list[UnifiedMessage]
    system_prompt: str | None = None
    tools: list[ToolCall] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class EvalResult(BaseModel):
    provider: str
    model: str
    score: float
    reasoning: str
    response: NormalizedResponse


class EvalService:
    async def evaluate(self, request: EvalRequest) -> list[EvalResult]:
        capabilities = [
            self._resolve_model(model_name) for model_name in request.models
        ]
        results = await asyncio.gather(
            *[
                self._evaluate_model(
                    capability=capability,
                    request=request,
                )
                for capability in capabilities
            ]
        )
        return sorted(results, key=lambda result: result.score, reverse=True)

    async def _evaluate_model(
        self,
        *,
        capability: ModelCapability,
        request: EvalRequest,
    ) -> EvalResult:
        adapter = provider_registry.get(capability.provider)
        unified_request = UnifiedRequest(
            model=capability.model,
            messages=request.messages,
            system_prompt=request.system_prompt,
            tools=request.tools,
            attachments=request.attachments,
            metadata=request.metadata,
        )
        provider_request = adapter.normalize_request(unified_request)
        normalized_request = NormalizedRequest(
            provider=capability.provider,
            request=provider_request,
            unified=unified_request,
        )
        response = await adapter.complete(normalized_request)
        score = self._score_response(response)
        reasoning = self._explain_score(response, score)
        return EvalResult(
            provider=capability.provider,
            model=capability.model,
            score=score,
            reasoning=reasoning,
            response=response,
        )

    @staticmethod
    def _score_response(response: NormalizedResponse) -> float:
        base = float(len(response.content.strip()))
        if response.finish_reason == "stop":
            base += 5.0
        if response.finish_reason == "stubbed":
            base += 1.0
        return round(base, 2)

    @staticmethod
    def _explain_score(response: NormalizedResponse, score: float) -> str:
        content_size = len(response.content.strip())
        finish_reason = response.finish_reason or "unknown"
        return (
            f"Scored {score} based on response length {content_size} "
            f"and finish reason '{finish_reason}'."
        )

    @staticmethod
    def _resolve_model(model_name: str) -> ModelCapability:
        if ":" in model_name:
            provider, model = model_name.split(":", 1)
            capability = capability_registry.get(provider, model)
            if capability is not None:
                return capability

        for capability in capability_registry.list():
            if capability.model == model_name:
                return capability

        raise ValueError(f"Model not found: {model_name}")


eval_service = EvalService()
