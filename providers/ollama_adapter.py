from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from providers._base_http import HttpProviderAdapter
from providers.base.adapter import (
    NormalizedRequest,
    NormalizedResponse,
    ProviderRequest,
    StreamChunk,
    ToolCall,
    UnifiedRequest,
)


class OllamaAdapter(HttpProviderAdapter):
    provider_name = "ollama"
    healthcheck_target = "LOCAL_OLLAMA_BASE_URL"
    _STREAM_TIMEOUT = 300.0

    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest:
        model = unified.model
        if model.startswith("ollama:"):
            model = model[len("ollama:"):]
        messages: list[dict[str, Any]] = []
        if unified.system_prompt:
            messages.append({"role": "system", "content": unified.system_prompt})
        for msg in unified.messages:
            content: Any = msg.content
            if unified.attachments:
                parts: list[dict[str, Any]] = [{"type": "text", "text": msg.content}]
                for att in unified.attachments:
                    if att.get("type") == "image":
                        parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{att['media_type']};base64,{att['data']}"
                            },
                        })
                content = parts
            messages.append({"role": msg.role, "content": content})
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if unified.tool_definitions:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": td.name,
                        "description": td.description,
                        "parameters": td.parameters,
                    },
                }
                for td in unified.tool_definitions
            ]
            # Force the model to output a tool call when requested.
            # Ollama follows the OpenAI tool_choice spec: "required" or {"type":"function","function":{"name":"..."}}
            tool_choice = unified.metadata.get("tool_choice")
            if tool_choice == "required":
                payload["tool_choice"] = "required"
        return ProviderRequest(model=unified.model, payload=payload)

    def normalize_response(self, raw: Any) -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        message = raw.get("message") or {}
        raw_tool_calls = message.get("tool_calls") or []
        tool_calls = [
            ToolCall(
                name=tc.get("function", {}).get("name", ""),
                arguments=tc.get("function", {}).get("arguments") or {},
            )
            for tc in raw_tool_calls
        ]
        content = message.get("content") or ""
        # Fallback: some models emit tool calls as JSON text in content (with or without markdown fences)
        if not tool_calls:
            stripped = content.strip()
            if stripped.startswith("{") or stripped.startswith("[") or stripped.startswith("```"):
                tool_calls = self._parse_text_tool_calls(content)
                if tool_calls:
                    content = ""
        finish_reason = "tool_calls" if tool_calls else ("stop" if raw.get("done", True) else None)
        return NormalizedResponse(
            provider=self.provider_name,
            model=raw.get("model", ""),
            content=content,
            finish_reason=finish_reason,
            usage=raw.get("usage", {}),
            raw_response=raw,
            tool_calls=tool_calls,
        )

    @staticmethod
    def _parse_text_tool_calls(text: str) -> list[ToolCall]:
        import re
        # Strip markdown code fences: ```json ... ``` or ``` ... ```
        stripped = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        if not stripped.startswith("{") and not stripped.startswith("["):
            return []
        try:
            obj = json.loads(stripped)
        except Exception:
            return []

        def _to_tool_call(d: dict) -> ToolCall | None:
            # Standard format: {"name": "...", "arguments": {...}}
            if "name" in d:
                return ToolCall(name=d["name"], arguments=d.get("arguments") or {})
            # Alternate format: {"command": "tool_name", ...other_keys_are_args}
            if "command" in d:
                args = {k: v for k, v in d.items() if k != "command"}
                return ToolCall(name=d["command"], arguments=args)
            # Alternate format: {"tool": "...", "parameters": {...}}
            if "tool" in d:
                return ToolCall(name=d["tool"], arguments=d.get("parameters") or d.get("arguments") or {})
            return None

        if isinstance(obj, dict):
            tc = _to_tool_call(obj)
            return [tc] if tc else []
        if isinstance(obj, list):
            return [tc for item in obj if isinstance(item, dict) for tc in [_to_tool_call(item)] if tc]
        return []

    def _path(self, request: NormalizedRequest) -> str:
        return "/api/chat"

    async def _stream_response(
        self, request: NormalizedRequest
    ) -> AsyncIterator[StreamChunk]:
        httpx = self._load_httpx()
        from core.config import get_settings
        settings = get_settings()
        url = f"{self._base_url(settings=settings)}/api/chat"
        payload = dict(request.request.payload)
        payload["stream"] = True
        async with httpx.AsyncClient(timeout=self._STREAM_TIMEOUT) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = (data.get("message") or {}).get("content", "")
                    if delta:
                        yield StreamChunk(delta=delta)
                    if data.get("done"):
                        yield StreamChunk(delta="", finish_reason="stop")
                        return
