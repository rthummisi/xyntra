from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
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

router = APIRouter(prefix="/compare", tags=["compare"])


class CompareRequest(BaseModel):
    models: list[str] = Field(min_length=2)
    messages: list[UnifiedMessage]
    system_prompt: str | None = None
    tools: list[ToolCall] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CompareResult(BaseModel):
    provider: str
    model: str
    response: NormalizedResponse


class CompareResponse(BaseModel):
    results: list[CompareResult]


@router.post("", response_model=CompareResponse)
async def compare_outputs(payload: CompareRequest) -> CompareResponse:
    try:
        capabilities = [_resolve_model(model_name) for model_name in payload.models]
    except HTTPException:
        raise
    results = await asyncio.gather(
        *[
            _run_model(
                capability=capability,
                payload=payload,
            )
            for capability in capabilities
        ]
    )
    return CompareResponse(results=results)


async def _run_model(
    *,
    capability: ModelCapability,
    payload: CompareRequest,
) -> CompareResult:
    adapter = provider_registry.get(capability.provider)
    request = UnifiedRequest(
        model=capability.model,
        messages=payload.messages,
        system_prompt=payload.system_prompt,
        tools=payload.tools,
        attachments=payload.attachments,
        metadata=payload.metadata,
    )
    provider_request = adapter.normalize_request(request)
    normalized_request = NormalizedRequest(
        provider=capability.provider,
        request=provider_request,
        unified=request,
    )
    response = await adapter.complete(normalized_request)
    return CompareResult(
        provider=capability.provider,
        model=capability.model,
        response=response,
    )


def _resolve_model(model_name: str) -> ModelCapability:
    if ":" in model_name:
        provider, model = model_name.split(":", 1)
        capability = capability_registry.get(provider, model)
        if capability is not None:
            return capability

    for capability in capability_registry.list():
        if capability.model == model_name:
            return capability

    raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
