from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from providers.base.adapter import (
    NormalizedResponse,
    StreamChunk,
    ToolCall,
    UnifiedMessage,
    UnifiedRequest,
)
from services.routing_service import RoutingDecision, routing_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    model: str
    messages: list[UnifiedMessage]
    system_prompt: str | None = None
    tools: list[ToolCall] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    strategy: str | None = None
    local_only: bool = False
    token_quota: int | None = None
    max_latency_ms: int | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    decision: RoutingDecision
    response: NormalizedResponse


@router.post("", response_model=ChatResponse)
async def create_chat_completion(
    payload: ChatRequest,
) -> ChatResponse | StreamingResponse:
    request = UnifiedRequest(
        model=payload.model,
        messages=payload.messages,
        system_prompt=payload.system_prompt,
        tools=payload.tools,
        attachments=payload.attachments,
        metadata=payload.metadata,
    )
    if payload.stream:
        try:
            decision, stream = routing_service.stream_route(
                request,
                strategy=payload.strategy,
                local_only=payload.local_only,
                token_quota=payload.token_quota,
                max_latency_ms=payload.max_latency_ms,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StreamingResponse(
            _sse_stream(decision, stream),
            media_type="text/event-stream",
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
    return ChatResponse(decision=decision, response=response)


async def _sse_stream(
    decision: RoutingDecision,
    stream: AsyncIterator[StreamChunk],
) -> AsyncIterator[str]:
    yield _sse_event("decision", decision.model_dump())
    async for chunk in stream:
        yield _sse_event("chunk", chunk.model_dump())
    yield _sse_event("done", {"status": "completed"})


def _sse_event(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"
