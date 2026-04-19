from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel
from redis.asyncio import Redis

from core.redis import redis_client


class SemanticCacheResult(BaseModel):
    hit: bool
    key: str
    value: str | None = None
    local_only: bool = False


class SemanticCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @staticmethod
    def build_key(
        *,
        normalized_prompt: str,
        model_family: str,
        system_prompt: str | None,
    ) -> str:
        prompt_hash = hashlib.sha256(normalized_prompt.encode("utf-8")).hexdigest()
        system_hash = hashlib.sha256((system_prompt or "").encode("utf-8")).hexdigest()
        return f"semantic:{model_family}:{prompt_hash}:{system_hash}"

    async def get(
        self,
        *,
        normalized_prompt: str,
        model_family: str,
        system_prompt: str | None,
        local_only: bool = False,
    ) -> SemanticCacheResult:
        key = self.build_key(
            normalized_prompt=normalized_prompt,
            model_family=model_family,
            system_prompt=system_prompt,
        )
        raw = await self.redis.get(key)
        if raw is None:
            return SemanticCacheResult(hit=False, key=key)

        payload = json.loads(raw)
        if local_only and not payload.get("local_only", False):
            return SemanticCacheResult(hit=False, key=key)

        return SemanticCacheResult(
            hit=True,
            key=key,
            value=payload.get("response"),
            local_only=payload.get("local_only", False),
        )

    async def set(
        self,
        *,
        normalized_prompt: str,
        model_family: str,
        system_prompt: str | None,
        response: str,
        local_only: bool = False,
    ) -> str:
        key = self.build_key(
            normalized_prompt=normalized_prompt,
            model_family=model_family,
            system_prompt=system_prompt,
        )
        await self.redis.set(
            key,
            json.dumps({"response": response, "local_only": local_only}),
            ex=3600,
        )
        return key


semantic_cache = SemanticCache(redis_client)
