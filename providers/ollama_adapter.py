from __future__ import annotations

from typing import Any

from providers._base_http import HttpProviderAdapter
from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    ProviderRequest,
    UnifiedRequest,
)


class OllamaAdapter(HttpProviderAdapter):
    provider_name = "ollama"
    healthcheck_target = "LOCAL_OLLAMA_BASE_URL"

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        prompt_parts: list[str] = []
        if unified.system_prompt:
            prompt_parts.append(unified.system_prompt)
        prompt_parts.extend(message.content for message in unified.messages)
        payload = {
            "model": unified.model,
            "prompt": "\n".join(prompt_parts),
            "stream": False,
            "options": unified.metadata,
        }
        if unified.tools:
            payload["tools"] = [
                {"name": tool.name, "parameters": tool.arguments}
                for tool in unified.tools
            ]
        if unified.attachments:
            payload["images"] = [
                attachment.get("content", "")
                for attachment in unified.attachments
                if attachment.get("kind") == "image"
            ]
            payload["attachments"] = unified.attachments
        return ProviderRequest(model=unified.model, payload=payload)

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        message = raw.get("message") or {}
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content=message.get("content", raw.get("response", raw.get("content", ""))),
            finish_reason="stop" if raw.get("done", True) else None,
            usage=raw.get("usage", {}),
            raw_response=raw,
        )

    def _path(self, request: NormalizedRequest) -> str:
        return "/api/generate"
