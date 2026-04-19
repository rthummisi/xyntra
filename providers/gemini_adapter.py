from __future__ import annotations

from typing import Any

from providers._base_http import HttpProviderAdapter
from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    ProviderRequest,
    UnifiedRequest,
)


class GeminiAdapter(HttpProviderAdapter):
    provider_name = "gemini"
    healthcheck_target = "GEMINI_API_KEY"

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        contents = []
        if unified.system_prompt:
            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": unified.system_prompt}],
                }
            )
        contents.extend(
            {
                "role": "model" if message.role == "assistant" else "user",
                "parts": [{"text": message.content}],
            }
            for message in unified.messages
        )
        payload = {
            "contents": contents,
            "tools": [
                {
                    "functionDeclarations": [
                        {
                            "name": tool.name,
                            "parameters": tool.arguments,
                        }
                    ]
                }
                for tool in unified.tools
            ],
            "generationConfig": {"candidateCount": 1},
            "metadata": unified.metadata,
        }
        if "temperature" in unified.metadata:
            payload["generationConfig"]["temperature"] = unified.metadata["temperature"]
        if "max_tokens" in unified.metadata:
            payload["generationConfig"]["maxOutputTokens"] = unified.metadata[
                "max_tokens"
            ]
        if unified.attachments:
            payload["attachments"] = unified.attachments
        return ProviderRequest(model=unified.model, payload=payload)

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        candidates = raw.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = "".join(part.get("text", "") for part in parts)
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content=text or raw.get("content", ""),
            finish_reason=(candidates[0].get("finishReason") if candidates else None),
            usage=raw.get("usageMetadata", raw.get("usage", {})),
            raw_response=raw,
        )

    def _path(self, request: NormalizedRequest) -> str:
        return f"/v1beta/models/{request.request.model}:generateContent"

    def _request_headers(self, *, settings) -> dict[str, str]:
        return {"content-type": "application/json"}

    def _request_params(
        self,
        request: NormalizedRequest,
        *,
        settings,
    ) -> dict[str, Any]:
        return {"key": self._api_key(settings=settings)}
