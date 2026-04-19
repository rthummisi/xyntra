from __future__ import annotations

import hashlib
import json
import uuid

import httpx
from sqlalchemy import select

from core.config import get_settings
from core.database import AsyncSessionLocal
from models.semantic_cache import SemanticCacheEntry

settings = get_settings()


class SemanticCacheService:
    @staticmethod
    def system_prompt_hash(system_prompt: str | None) -> str:
        return hashlib.sha256((system_prompt or "").encode("utf-8")).hexdigest()

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient(
            base_url=settings.local_ollama_base_url,
            timeout=settings.provider_timeout_seconds,
        ) as client:
            response = await client.post(
                "/api/embed",
                json={
                    "model": settings.semantic_cache_embedding_model,
                    "input": text,
                },
            )
            response.raise_for_status()
            payload = response.json()
        embeddings = payload.get("embeddings") or []
        if not embeddings:
            raise ValueError("Embedding response was empty.")
        return [float(value) for value in embeddings[0]]

    async def persist_entry(
        self,
        *,
        project_id: uuid.UUID | None,
        normalized_prompt: str,
        model_family: str,
        system_prompt: str | None,
        response: str,
        local_only: bool,
    ) -> None:
        embedding = await self.embed_text(normalized_prompt)
        async with AsyncSessionLocal() as session:
            entry = SemanticCacheEntry(
                project_id=project_id,
                normalized_prompt=normalized_prompt,
                model_family=model_family,
                system_prompt_hash=self.system_prompt_hash(system_prompt),
                response_payload={"response": response, "local_only": local_only},
                embedding=embedding,
                generated_locally=local_only,
            )
            session.add(entry)
            await session.commit()

    async def find_similar_entry(
        self,
        *,
        normalized_prompt: str,
        model_family: str,
        system_prompt: str | None,
        local_only: bool,
        similarity_threshold: float | None = None,
    ) -> tuple[SemanticCacheEntry | None, float | None]:
        threshold = (
            settings.semantic_cache_similarity_threshold
            if similarity_threshold is None
            else similarity_threshold
        )
        embedding = await self.embed_text(normalized_prompt)
        async with AsyncSessionLocal() as session:
            similarity = (1 - SemanticCacheEntry.embedding.cosine_distance(embedding)).label(
                "similarity"
            )
            query = (
                select(SemanticCacheEntry, similarity)
                .where(SemanticCacheEntry.model_family == model_family)
                .where(
                    SemanticCacheEntry.system_prompt_hash
                    == self.system_prompt_hash(system_prompt)
                )
                .where(SemanticCacheEntry.embedding.is_not(None))
                .order_by(similarity.desc())
            )
            if local_only:
                query = query.where(SemanticCacheEntry.generated_locally.is_(True))
            result = await session.execute(query)
            first = result.first()
            if first is None:
                return None, None
            entry, score = first
            similarity_score = float(score)
            if similarity_score < threshold:
                return None, similarity_score
            return entry, similarity_score

    async def list_entries(
        self,
        *,
        project_id: uuid.UUID | None = None,
        local_only: bool | None = None,
        limit: int = 50,
    ) -> list[SemanticCacheEntry]:
        async with AsyncSessionLocal() as session:
            query = select(SemanticCacheEntry).order_by(
                SemanticCacheEntry.created_at.desc()
            )
            if project_id is not None:
                query = query.where(SemanticCacheEntry.project_id == project_id)
            if local_only is not None:
                query = query.where(SemanticCacheEntry.generated_locally.is_(local_only))
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_entry_by_id(self, entry_id: uuid.UUID) -> SemanticCacheEntry | None:
        async with AsyncSessionLocal() as session:
            return await session.get(SemanticCacheEntry, entry_id)

    async def backfill_missing_embeddings(self, *, limit: int | None = None) -> int:
        async with AsyncSessionLocal() as session:
            query = (
                select(SemanticCacheEntry)
                .where(SemanticCacheEntry.embedding.is_(None))
                .order_by(SemanticCacheEntry.created_at.asc())
            )
            if limit is not None:
                query = query.limit(limit)
            result = await session.execute(query)
            entries = list(result.scalars().all())

            for entry in entries:
                entry.embedding = await self.embed_text(entry.normalized_prompt)

            await session.commit()
            return len(entries)

    @staticmethod
    def extract_response(entry: SemanticCacheEntry) -> str | None:
        payload = entry.response_payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return payload
        return payload.get("response") if isinstance(payload, dict) else None


semantic_cache_service = SemanticCacheService()
