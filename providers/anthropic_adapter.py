from __future__ import annotations

from typing import Any

from providers._base_http import HttpProviderAdapter
from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    ProviderRequest,
    UnifiedRequest,
)


class AnthropicAdapter(HttpProviderAdapter):
    provider_name = "anthropic"
    healthcheck_target = "ANTHROPIC_API_KEY"

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        payload = {
            "model": unified.model,
            "max_tokens": int(unified.metadata.get("max_tokens", 1024)),
            "messages": [
                {
                    "role": message.role,
                    "content": [{"type": "text", "text": message.content}],
                }
                for message in unified.messages
            ],
            "tools": [
                {
                    "name": tool.name,
                    "input_schema": tool.arguments,
                }
                for tool in unified.tools
            ],
            "metadata": unified.metadata,
        }
        if unified.system_prompt:
            payload["system"] = unified.system_prompt
        if unified.attachments:
            payload["attachments"] = unified.attachments
        return ProviderRequest(model=unified.model, payload=payload)

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        content_blocks = raw.get("content", [])
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content="".join(text_parts) or raw.get("content", ""),
            finish_reason=raw.get("stop_reason", raw.get("finish_reason")),
            usage=raw.get("usage", {}),
            raw_response=raw,
        )

    def _path(self, request: NormalizedRequest) -> str:
        return "/v1/messages"

    def _request_headers(self, *, settings) -> dict[str, str]:
        headers = super()._request_headers(settings=settings)
        headers["x-api-key"] = self._api_key(settings=settings)
        headers.pop("authorization", None)
        headers["anthropic-version"] = "2023-06-01"
        return headers
