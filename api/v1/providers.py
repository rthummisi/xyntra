from __future__ import annotations

import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

from providers.capability_registry import ModelCapability, capability_registry
from providers.registry import provider_registry
from routing.circuit_breaker import circuit_breaker

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderSummary(BaseModel):
    provider: str
    models: list[str]
    local_only: bool


class ProviderHealthResponse(BaseModel):
    provider: str
    status: str
    details: dict


class ProviderCapabilityResponse(BaseModel):
    provider: str
    model: str
    context_window: int
    quality_tier: str
    supports_streaming: bool
    supports_tools: bool
    supports_images: bool
    supports_pdf: bool
    local_only: bool
    cost_tier: str
    latency_tier: str


class LeaderboardEntry(BaseModel):
    provider: str
    model: str
    quality_tier: str
    cost_tier: str
    latency_tier: str
    context_window: int
    supports_images: bool
    supports_pdf: bool
    local_only: bool


@router.get("", response_model=list[ProviderSummary])
async def list_providers() -> list[ProviderSummary]:
    summaries: list[ProviderSummary] = []
    for adapter in provider_registry.list():
        capabilities = capability_registry.by_provider(adapter.provider_name)
        summaries.append(
            ProviderSummary(
                provider=adapter.provider_name,
                models=sorted(capability.model for capability in capabilities),
                local_only=(
                    all(capability.local_only for capability in capabilities)
                    if capabilities
                    else False
                ),
            )
        )
    return summaries


@router.get("/health", response_model=list[ProviderHealthResponse])
async def list_provider_health() -> list[ProviderHealthResponse]:
    results = await asyncio.gather(
        *[adapter.health_check() for adapter in provider_registry.list()]
    )
    states = {state.provider: state for state in circuit_breaker.get_states()}
    payload: list[ProviderHealthResponse] = []
    for result in results:
        details = dict(result.details)
        state = states.get(result.provider)
        if state is not None:
            details["circuit_healthy"] = state.healthy
            details["circuit_failures"] = state.failures
        payload.append(
            ProviderHealthResponse(
                provider=result.provider,
                status=result.status,
                details=details,
            )
        )
    return payload


@router.get("/capabilities", response_model=list[ProviderCapabilityResponse])
async def list_provider_capabilities(
    provider: str | None = None,
) -> list[ProviderCapabilityResponse]:
    capabilities = (
        capability_registry.by_provider(provider)
        if provider is not None
        else capability_registry.list()
    )
    return [_serialize_capability(capability) for capability in capabilities]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_model_leaderboard() -> list[LeaderboardEntry]:
    capabilities = sorted(
        capability_registry.list(),
        key=lambda capability: (
            _quality_rank(capability.quality_tier),
            _cost_rank(capability.cost_tier),
            _latency_rank(capability.latency_tier),
            -capability.context_window,
            capability.provider,
            capability.model,
        ),
    )
    return [
        LeaderboardEntry(
            provider=capability.provider,
            model=capability.model,
            quality_tier=capability.quality_tier,
            cost_tier=capability.cost_tier,
            latency_tier=capability.latency_tier,
            context_window=capability.context_window,
            supports_images=capability.supports_images,
            supports_pdf=capability.supports_pdf,
            local_only=capability.local_only,
        )
        for capability in capabilities
    ]


def _serialize_capability(
    capability: ModelCapability,
) -> ProviderCapabilityResponse:
    return ProviderCapabilityResponse(**capability.model_dump())


def _quality_rank(quality_tier: str) -> int:
    ranking = {
        "premium": 0,
        "high": 1,
        "medium": 2,
        "local": 3,
        "embedding": 4,
    }
    return ranking.get(quality_tier, 99)


def _cost_rank(cost_tier: str) -> int:
    ranking = {
        "economy": 0,
        "standard": 1,
        "premium": 2,
        "local": 3,
    }
    return ranking.get(cost_tier, 99)


def _latency_rank(latency_tier: str) -> int:
    ranking = {
        "fast": 0,
        "local": 1,
        "standard": 2,
    }
    return ranking.get(latency_tier, 99)
