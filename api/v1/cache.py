from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.semantic_cache_service import semantic_cache_service

router = APIRouter(prefix="/cache", tags=["cache"])


class SemanticCacheEntryResponse(BaseModel):
    id: str
    project_id: str | None = None
    key: str
    normalized_prompt: str
    model_family: str
    system_prompt_hash: str
    response: str | None = None
    local_only: bool = False
    has_embedding: bool = False


@router.get("/semantic", response_model=list[SemanticCacheEntryResponse])
async def list_semantic_cache_entries(
    project_id: uuid.UUID | None = None,
    local_only: bool | None = None,
    limit: int = 50,
) -> list[SemanticCacheEntryResponse]:
    entries = await semantic_cache_service.list_entries(
        project_id=project_id,
        local_only=local_only,
        limit=limit,
    )
    return [_serialize_entry(entry) for entry in entries]


@router.get("/semantic/{entry_id}", response_model=SemanticCacheEntryResponse)
async def get_semantic_cache_entry(entry_id: uuid.UUID) -> SemanticCacheEntryResponse:
    entry = await semantic_cache_service.get_entry_by_id(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Semantic cache entry not found.")
    return _serialize_entry(entry)


def _serialize_entry(entry) -> SemanticCacheEntryResponse:
    return SemanticCacheEntryResponse(
        id=str(entry.id),
        project_id=None if entry.project_id is None else str(entry.project_id),
        key=f"{entry.model_family}:{entry.system_prompt_hash}",
        normalized_prompt=entry.normalized_prompt,
        model_family=entry.model_family,
        system_prompt_hash=entry.system_prompt_hash,
        response=semantic_cache_service.extract_response(entry),
        local_only=entry.generated_locally,
        has_embedding=entry.embedding is not None,
    )
