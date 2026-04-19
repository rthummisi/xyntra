from __future__ import annotations

from typing import Any

from providers._base_http import HttpProviderAdapter
from providers.base.adapter import (
    NormalizedResponse,
    ProviderRequest,
    ToolCall,
    UnifiedRequest,
)


class OpenAIAdapter(HttpProviderAdapter):
    provider_name = "openai"
    healthcheck_target = "OPENAI_API_KEY"

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        payload = {
            "model": unified.model,
            "messages": [],
            "tools": [],
            "metadata": unified.metadata,
        }
        if unified.system_prompt:
            payload["messages"].append(
                {"role": "system", "content": unified.system_prompt}
            )
        payload["messages"].extend(
            {"role": message.role, "content": message.content}
            for message in unified.messages
        )
        if unified.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "arguments": tool.arguments,
                    },
                }
                for tool in unified.tools
            ]
        if unified.attachments:
            payload["attachments"] = unified.attachments
        if "temperature" in unified.metadata:
            payload["temperature"] = unified.metadata["temperature"]
        if "max_tokens" in unified.metadata:
            payload["max_tokens"] = unified.metadata["max_tokens"]
        return ProviderRequest(model=unified.model, payload=payload)

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        choice = (raw.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        tool_calls = [
            ToolCall(
                name=call.get("function", {}).get("name", ""),
                arguments=call.get("function", {}).get("arguments", {}) or {},
            )
            for call in message.get("tool_calls", [])
        ]
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content=message.get("content", raw.get("content", "")) or "",
            finish_reason=choice.get("finish_reason", raw.get("finish_reason")),
            usage=raw.get("usage", {}),
            raw_response=raw,
            tool_calls=tool_calls,
        )
