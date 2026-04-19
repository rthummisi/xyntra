from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from core.config import Settings, get_settings
from providers.base.adapter import (
    BaseAdapter,
    NormalizedRequest,
    NormalizedResponse,
    ProviderHealth,
    ProviderRequest,
    StreamChunk,
    UnifiedRequest,
)


class HttpProviderAdapter(BaseAdapter):
    provider_name = "stub"
    healthcheck_target = "configured"

    async def complete(self, request: NormalizedRequest) -> NormalizedResponse:
        response = await self._send_request(request, stream=False)
        return self.normalize_response(response)

    async def stream(
        self,
        request: NormalizedRequest,
    ) -> AsyncIterator[StreamChunk]:
        try:
            async for chunk in self._stream_response(request):
                yield chunk
            return
        except NotImplementedError:
            pass

        response = await self.complete(request)
        if response.content:
            yield StreamChunk(delta=response.content)
        yield StreamChunk(delta="", finish_reason=response.finish_reason or "stop")

    async def health_check(self) -> ProviderHealth:
        details = self._health_details()
        return ProviderHealth(
            provider=self.provider_name,
            status="ok" if details["configured"] else "degraded",
            details=details,
        )

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        return ProviderRequest(
            model=unified.model,
            payload={
                "messages": [message.model_dump() for message in unified.messages],
                "system_prompt": unified.system_prompt,
                "tools": [tool.model_dump() for tool in unified.tools],
                "attachments": unified.attachments,
                "metadata": unified.metadata,
            },
        )

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content=raw.get("content", ""),
            finish_reason=raw.get("finish_reason"),
            usage=raw.get("usage", {}),
            raw_response=raw,
        )

    async def _send_request(
        self,
        request: NormalizedRequest,
        *,
        stream: bool,
    ) -> dict[str, Any]:
        httpx = self._load_httpx()
        settings = get_settings()
        kwargs = self._request_kwargs(request, settings=settings, stream=stream)
        timeout = kwargs.pop("timeout", settings.provider_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(**kwargs)
            response.raise_for_status()
            return response.json()

    def _stream_response(
        self,
        request: NormalizedRequest,
    ) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError

    def _request_kwargs(
        self,
        request: NormalizedRequest,
        *,
        settings: Settings,
        stream: bool,
    ) -> dict[str, Any]:
        payload = dict(request.request.payload)
        if stream:
            payload["stream"] = True
        return {
            "method": "POST",
            "url": self._request_url(request, settings=settings),
            "headers": self._request_headers(settings=settings),
            "json": payload,
            "params": self._request_params(request, settings=settings),
        }

    def _request_url(
        self,
        request: NormalizedRequest,
        *,
        settings: Settings,
    ) -> str:
        return f"{self._base_url(settings=settings)}{self._path(request)}"

    def _request_params(
        self,
        request: NormalizedRequest,
        *,
        settings: Settings,
    ) -> dict[str, Any]:
        return {}

    def _request_headers(self, *, settings: Settings) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        api_key = self._api_key(settings=settings)
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        return headers

    def _base_url(self, *, settings: Settings) -> str:
        setting_name = (
            "local_ollama_base_url"
            if self.provider_name == "ollama"
            else f"{self.provider_name}_base_url"
        )
        return str(getattr(settings, setting_name)).rstrip("/")

    def _api_key(self, *, settings: Settings) -> str:
        key_name = f"{self.provider_name}_api_key"
        return str(getattr(settings, key_name, ""))

    def _path(self, request: NormalizedRequest) -> str:
        return "/v1/chat/completions"

    def _health_details(self) -> dict[str, Any]:
        configured = self._is_configured()
        return {
            "configured": configured,
            "target": self.healthcheck_target,
            "base_url": self._base_url(settings=get_settings()),
        }

    def _is_configured(self) -> bool:
        settings = get_settings()
        if self.provider_name == "ollama":
            return bool(settings.local_ollama_base_url)
        return bool(self._api_key(settings=settings))

    @staticmethod
    def _load_httpx():
        import httpx

        return httpx
