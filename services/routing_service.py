from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from context.semantic_cache import semantic_cache
from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    UnifiedRequest,
)
from providers.capability_registry import ModelCapability, capability_registry
from providers.registry import provider_registry
from routing.budgeter import budget_enforcer
from routing.circuit_breaker import circuit_breaker
from routing.classifier import routing_classifier
from routing.context_escalator import context_escalator
from routing.fallback import build_fallback_chain
from routing.latency_sla import latency_sla_enforcer
from routing.strategies import strategy_selector
from services.policy_service import PolicyEvaluation, policy_service
from services.semantic_cache_service import semantic_cache_service

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from providers.base.adapter import BaseAdapter, StreamChunk


class RoutingDecision(BaseModel):
    selected_provider: str
    selected_model: str
    classification: dict
    fallback_chain: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


@dataclass
class PreparedRoute:
    decision: RoutingDecision
    adapter: BaseAdapter
    normalized_request: NormalizedRequest
    policy: PolicyEvaluation


class RoutingService:
    async def route(
        self,
        request: UnifiedRequest,
        *,
        strategy: str | None = None,
        local_only: bool = False,
        token_quota: int | None = None,
        max_latency_ms: int | None = None,
    ) -> tuple[RoutingDecision, NormalizedResponse]:
        prepared = self._prepare_route(
            request,
            strategy=strategy,
            local_only=local_only,
            token_quota=token_quota,
            max_latency_ms=max_latency_ms,
        )
        cached = await self._get_cached_response(
            request,
            provider_name=prepared.decision.selected_provider,
            model_name=prepared.decision.selected_model,
            local_only=local_only,
        )
        if cached is not None:
            prepared.decision.metadata["cache_hit"] = True
            return prepared.decision, cached
        try:
            response = await prepared.adapter.complete(prepared.normalized_request)
        except Exception:
            circuit_breaker.record_failure(prepared.decision.selected_provider)
            raise
        await self._store_cached_response(
            request,
            model_name=prepared.decision.selected_model,
            response=response.content,
            local_only=local_only,
        )
        circuit_breaker.record_success(prepared.decision.selected_provider)
        prepared.decision.metadata["cache_hit"] = False
        return prepared.decision, response

    def stream_route(
        self,
        request: UnifiedRequest,
        *,
        strategy: str | None = None,
        local_only: bool = False,
        token_quota: int | None = None,
        max_latency_ms: int | None = None,
    ) -> tuple[RoutingDecision, AsyncIterator[StreamChunk]]:
        prepared = self._prepare_route(
            request,
            strategy=strategy,
            local_only=local_only,
            token_quota=token_quota,
            max_latency_ms=max_latency_ms,
        )

        async def _stream() -> AsyncIterator[StreamChunk]:
            try:
                async for chunk in prepared.adapter.stream(prepared.normalized_request):
                    yield chunk
            except Exception:
                circuit_breaker.record_failure(prepared.decision.selected_provider)
                raise
            circuit_breaker.record_success(prepared.decision.selected_provider)

        return prepared.decision, _stream()

    def _prepare_route(
        self,
        request: UnifiedRequest,
        *,
        strategy: str | None,
        local_only: bool,
        token_quota: int | None,
        max_latency_ms: int | None,
    ) -> PreparedRoute:
        classification = routing_classifier.classify(request)
        estimated_tokens = self._estimate_tokens(request)
        prompt_text = self._build_policy_text(request)
        base_policy = policy_service.evaluate_routing(
            text=prompt_text,
            provider_name="ollama" if local_only else "openai",
            local_only=local_only,
            token_quota=token_quota,
            estimated_tokens=estimated_tokens,
            task_type=classification.task_type,
        )
        if not base_policy.allowed:
            raise ValueError(
                base_policy.reasons[0] if base_policy.reasons else "PolicyViolation"
            )
        budget = budget_enforcer.evaluate(
            token_quota=token_quota,
            estimated_tokens=estimated_tokens,
        )
        if not budget.allowed:
            raise ValueError(budget.reason or "QuotaExceeded")

        candidates = self._filter_candidates(
            classification=classification,
            local_only=local_only,
            requested_model=request.model,
        )
        candidates = [
            candidate
            for candidate in candidates
            if policy_service.evaluate_routing(
                text=prompt_text,
                provider_name=candidate.provider,
                local_only=local_only,
                token_quota=token_quota,
                estimated_tokens=estimated_tokens,
                task_type=classification.task_type,
            ).allowed
        ]
        ordered = strategy_selector.apply(classification, candidates, strategy=strategy)
        available = [
            candidate
            for candidate in ordered
            if circuit_breaker.is_available(candidate.provider)
        ]
        if not available:
            raise ValueError("No available providers.")

        chosen = self._select_candidate(
            available,
            estimated_tokens=estimated_tokens,
            max_latency_ms=max_latency_ms,
        )
        policy = policy_service.evaluate_routing(
            text=prompt_text,
            provider_name=chosen.provider,
            local_only=local_only,
            token_quota=token_quota,
            estimated_tokens=estimated_tokens,
            task_type=classification.task_type,
        )
        fallback_chain = build_fallback_chain(available)
        adapter = provider_registry.get(chosen.provider)
        provider_request = adapter.normalize_request(
            self._redacted_request(request, policy.redacted_text)
        )
        normalized_request = NormalizedRequest(
            provider=chosen.provider,
            request=provider_request,
            unified=request,
        )
        decision = RoutingDecision(
            selected_provider=chosen.provider,
            selected_model=chosen.model,
            classification=classification.model_dump(),
            fallback_chain=[
                f"{candidate.provider}:{candidate.model}"
                for candidate in fallback_chain
            ],
            metadata={
                "estimated_tokens": estimated_tokens,
                "approval_required": policy.approval_required,
                "policy_reasons": policy.reasons,
                "redacted_text": policy.redacted_text,
            },
        )
        return PreparedRoute(
            decision=decision,
            adapter=adapter,
            normalized_request=normalized_request,
            policy=policy,
        )

    def _filter_candidates(
        self,
        *,
        classification,
        local_only: bool,
        requested_model: str | None = None,
    ) -> list[ModelCapability]:
        candidates: list[ModelCapability] = []
        requested_capability = self._resolve_requested_model(requested_model)
        for capability in capability_registry.list():
            if local_only and not capability.local_only:
                continue
            if requested_capability is not None and (
                capability.provider != requested_capability.provider
                or capability.model != requested_capability.model
            ):
                continue
            if classification.requires_multimodal and not (
                capability.supports_images or capability.supports_pdf
            ):
                continue
            if classification.requires_tools and not capability.supports_tools:
                continue
            candidates.append(capability)
        return candidates

    def _select_candidate(
        self,
        candidates: list[ModelCapability],
        *,
        estimated_tokens: int,
        max_latency_ms: int | None,
    ) -> ModelCapability:
        for candidate in candidates:
            if context_escalator.needs_escalation(
                estimated_tokens=estimated_tokens,
                candidate=candidate,
            ):
                continue
            expected_latency = (
                500 if candidate.latency_tier in {"fast", "local"} else 1500
            )
            if latency_sla_enforcer.within_sla(
                expected_latency_ms=expected_latency,
                max_latency_ms=max_latency_ms,
            ):
                return candidate
        return candidates[-1]

    @staticmethod
    def _resolve_requested_model(model_name: str | None) -> ModelCapability | None:
        if not model_name:
            return None
        if ":" in model_name:
            provider_name, provider_model = model_name.split(":", 1)
            capability = capability_registry.get(provider_name, provider_model)
            if capability is not None:
                return capability
        for capability in capability_registry.list():
            if capability.model == model_name:
                return capability
        return None

    @staticmethod
    def _estimate_tokens(request: UnifiedRequest) -> int:
        total_text = " ".join(message.content for message in request.messages)
        total_text += f" {request.system_prompt or ''}"
        return max(1, len(total_text.split()))

    @staticmethod
    def _build_policy_text(request: UnifiedRequest) -> str:
        parts = [request.system_prompt or ""]
        parts.extend(message.content for message in request.messages)
        return "\n".join(part for part in parts if part)

    @staticmethod
    def _redacted_request(
        request: UnifiedRequest,
        redacted_text: str,
    ) -> UnifiedRequest:
        if not request.messages:
            return request
        redacted_messages = list(request.messages)
        redacted_messages[-1] = redacted_messages[-1].model_copy(
            update={"content": redacted_text}
        )
        return request.model_copy(update={"messages": redacted_messages})

    async def _get_cached_response(
        self,
        request: UnifiedRequest,
        *,
        provider_name: str,
        model_name: str,
        local_only: bool,
    ) -> NormalizedResponse | None:
        try:
            result = await semantic_cache.get(
                normalized_prompt=self._build_policy_text(request),
                model_family=model_name,
                system_prompt=request.system_prompt,
                local_only=local_only,
            )
        except Exception:
            result = None
        if result is not None and result.hit and result.value is not None:
            return NormalizedResponse(
                provider=provider_name,
                model=model_name,
                content=result.value,
                finish_reason="cache_hit",
                raw_response={"cache_key": result.key, "local_only": result.local_only},
            )
        similarity_score = None
        try:
            persisted, similarity_score = await semantic_cache_service.find_similar_entry(
                normalized_prompt=self._build_policy_text(request),
                model_family=model_name,
                system_prompt=request.system_prompt,
                local_only=local_only,
            )
        except Exception:
            return None
        if persisted is None:
            return None
        persisted_response = semantic_cache_service.extract_response(persisted)
        if persisted_response is None:
            return None
        try:
            await semantic_cache.set(
                normalized_prompt=self._build_policy_text(request),
                model_family=model_name,
                system_prompt=request.system_prompt,
                response=persisted_response,
                local_only=persisted.generated_locally,
            )
        except Exception:
            pass
        return NormalizedResponse(
            provider=provider_name,
            model=model_name,
            content=persisted_response,
            finish_reason="cache_hit",
            raw_response={
                "cache_key": semantic_cache.build_key(
                    normalized_prompt=self._build_policy_text(request),
                    model_family=model_name,
                    system_prompt=request.system_prompt,
                ),
                "local_only": persisted.generated_locally,
                "source": "database",
                "similarity": similarity_score,
            },
        )

    async def _store_cached_response(
        self,
        request: UnifiedRequest,
        *,
        model_name: str,
        response: str,
        local_only: bool,
    ) -> None:
        try:
            await semantic_cache.set(
                normalized_prompt=self._build_policy_text(request),
                model_family=model_name,
                system_prompt=request.system_prompt,
                response=response,
                local_only=local_only,
            )
        except Exception:
            pass
        try:
            await semantic_cache_service.persist_entry(
                project_id=self._resolve_project_id(request),
                normalized_prompt=self._build_policy_text(request),
                model_family=model_name,
                system_prompt=request.system_prompt,
                response=response,
                local_only=local_only,
            )
        except Exception:
            return

    @staticmethod
    def _resolve_project_id(request: UnifiedRequest) -> uuid.UUID | None:
        project_id = request.metadata.get("project_id")
        if project_id is None:
            return None
        if isinstance(project_id, uuid.UUID):
            return project_id
        try:
            return uuid.UUID(str(project_id))
        except ValueError:
            return None


routing_service = RoutingService()
