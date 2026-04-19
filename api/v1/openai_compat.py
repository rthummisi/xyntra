from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from providers.base.adapter import StreamChunk, ToolCall, UnifiedMessage, UnifiedRequest
from services.routing_service import routing_service

router = APIRouter(prefix="/v1", tags=["openai-compat"])


class OpenAIChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str
    messages: list[OpenAIChatMessage]
    stream: bool = False
    tools: list[ToolCall] = Field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict = Field(default_factory=dict)


class OpenAIChatChoiceMessage(BaseModel):
    role: str
    content: str


class OpenAIChatChoice(BaseModel):
    index: int
    message: OpenAIChatChoiceMessage
    finish_reason: str | None = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[OpenAIChatChoice]
    usage: OpenAIUsage


@router.post("/chat/completions", response_model=OpenAIChatResponse)
async def create_openai_chat_completion(
    payload: OpenAIChatRequest,
) -> OpenAIChatResponse | StreamingResponse:
    resolved_model = _resolve_openai_model(payload.model)
    metadata = dict(payload.metadata)
    if payload.temperature is not None:
        metadata["temperature"] = payload.temperature
    if payload.max_tokens is not None:
        metadata["max_tokens"] = payload.max_tokens
    request = UnifiedRequest(
        model=resolved_model,
        messages=[
            UnifiedMessage(role=message.role, content=message.content)
            for message in payload.messages
        ],
        tools=payload.tools,
        metadata=metadata,
    )
    if payload.stream:
        try:
            decision, stream = routing_service.stream_route(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        completion_id = _completion_id()
        created = int(time.time())
        return StreamingResponse(
            _openai_sse_stream(
                completion_id=completion_id,
                created=created,
                model=payload.model,
                stream=stream,
            ),
            media_type="text/event-stream",
        )

    try:
        _, response = await routing_service.route(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OpenAIChatResponse(
        id=_completion_id(),
        object="chat.completion",
        created=int(time.time()),
        model=payload.model,
        choices=[
            OpenAIChatChoice(
                index=0,
                message=OpenAIChatChoiceMessage(
                    role="assistant",
                    content=response.content,
                ),
                finish_reason=response.finish_reason or "stop",
            )
        ],
        usage=OpenAIUsage(**_normalize_usage(response.usage)),
    )


async def _openai_sse_stream(
    *,
    completion_id: str,
    created: int,
    model: str,
    stream: AsyncIterator[StreamChunk],
) -> AsyncIterator[str]:
    yield _openai_sse_chunk(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
        }
    )
    async for chunk in stream:
        yield _openai_sse_chunk(
            {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk.delta},
                        "finish_reason": chunk.finish_reason,
                    }
                ],
            }
        )
    yield "data: [DONE]\n\n"


def _openai_sse_chunk(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex}"


def _normalize_usage(usage: dict) -> dict:
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    completion_tokens = int(usage.get("completion_tokens", 0))
    total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _resolve_openai_model(model: str) -> str:
    aliases = {
        "gpt-4.1": "gpt-4o",
        "gpt-4.1-mini": "gpt-4o-mini",
        "gpt-4.1-nano": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4o",
    }
    return aliases.get(model, model)
