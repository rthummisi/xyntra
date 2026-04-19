from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from providers.base.adapter import NormalizedResponse, UnifiedMessage, UnifiedRequest
from services.routing_service import RoutingDecision, routing_service

router = APIRouter(prefix="/router", tags=["routing"])


class RouteRequest(BaseModel):
    model: str
    messages: list[UnifiedMessage]
    system_prompt: str | None = None
    attachments: list[dict] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    strategy: str | None = None
    local_only: bool = False
    token_quota: int | None = None
    max_latency_ms: int | None = None


class RouteResponse(BaseModel):
    decision: RoutingDecision
    response: NormalizedResponse


@router.post("", response_model=RouteResponse)
async def route_request(payload: RouteRequest) -> RouteResponse:
    request = UnifiedRequest(
        model=payload.model,
        messages=payload.messages,
        system_prompt=payload.system_prompt,
        attachments=payload.attachments,
        tools=payload.tools,
    )
    try:
        decision, response = await routing_service.route(
            request,
            strategy=payload.strategy,
            local_only=payload.local_only,
            token_quota=payload.token_quota,
            max_latency_ms=payload.max_latency_ms,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RouteResponse(decision=decision, response=response)
