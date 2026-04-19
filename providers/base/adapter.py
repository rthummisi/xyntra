from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class UnifiedMessage(BaseModel):
    role: str
    content: str


class UnifiedRequest(BaseModel):
    model: str
    messages: list[UnifiedMessage]
    system_prompt: str | None = None
    tools: list[ToolCall] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ProviderRequest(BaseModel):
    model: str
    payload: dict = Field(default_factory=dict)


class StreamChunk(BaseModel):
    delta: str = ""
    finish_reason: str | None = None
    metadata: dict = Field(default_factory=dict)


class NormalizedResponse(BaseModel):
    provider: str
    model: str
    content: str
    finish_reason: str | None = None
    usage: dict = Field(default_factory=dict)
    raw_response: dict = Field(default_factory=dict)
    tool_calls: list[ToolCall] = Field(default_factory=list)


class ProviderHealth(BaseModel):
    provider: str
    status: str
    details: dict = Field(default_factory=dict)


class NormalizedRequest(BaseModel):
    provider: str
    request: ProviderRequest
    unified: UnifiedRequest


class BaseAdapter(ABC):
    provider_name: str

    @abstractmethod
    async def complete(self, request: NormalizedRequest) -> NormalizedResponse: ...

    @abstractmethod
    async def stream(
        self,
        request: NormalizedRequest,
    ) -> AsyncIterator[StreamChunk]: ...

    @abstractmethod
    async def health_check(self) -> ProviderHealth: ...

    @abstractmethod
    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest: ...

    @abstractmethod
    def normalize_response(self, raw: Any) -> NormalizedResponse: ...
