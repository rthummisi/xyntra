from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import api_key_manager
from models import APIKey
from services.api_key_service import api_key_service

router = APIRouter(prefix="/security", tags=["security"])


class APIKeyCreateRequest(BaseModel):
    name: str
    ttl_days: int = 90


class APIKeyRotateRequest(BaseModel):
    ttl_days: int = 90


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key_id: str
    name: str
    token_preview: str
    issued_at: str
    expires_at: str
    revoked_at: str | None
    last_used_at: str | None
    expired: bool


class APIKeySecretResponse(BaseModel):
    api_key: APIKeyResponse
    raw_token: str


def _serialize(api_key: APIKey) -> APIKeyResponse:
    return APIKeyResponse(
        id=api_key.id,
        key_id=api_key.key_id,
        name=api_key.name,
        token_preview=api_key.token_preview,
        issued_at=api_key.issued_at.isoformat(),
        expires_at=api_key.expires_at.isoformat(),
        revoked_at=None if api_key.revoked_at is None else api_key.revoked_at.isoformat(),
        last_used_at=None
        if api_key.last_used_at is None
        else api_key.last_used_at.isoformat(),
        expired=api_key.revoked_at is not None
        or api_key_manager.is_expired(api_key.expires_at),
    )


@router.post("/api-keys", response_model=APIKeySecretResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: APIKeyCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> APIKeySecretResponse:
    raw_token, api_key = await api_key_service.create_key(
        db,
        name=payload.name,
        ttl_days=payload.ttl_days,
    )
    return APIKeySecretResponse(api_key=_serialize(api_key), raw_token=raw_token)


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db_session),
) -> list[APIKeyResponse]:
    keys = await api_key_service.list_keys(db)
    return [_serialize(item) for item in keys]


@router.post("/api-keys/{api_key_id}/rotate", response_model=APIKeySecretResponse)
async def rotate_api_key(
    api_key_id: uuid.UUID,
    payload: APIKeyRotateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> APIKeySecretResponse:
    api_key = await api_key_service.get_key(db, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    raw_token, rotated = await api_key_service.rotate_key(
        db,
        api_key=api_key,
        ttl_days=payload.ttl_days,
    )
    return APIKeySecretResponse(api_key=_serialize(rotated), raw_token=raw_token)


@router.post("/api-keys/{api_key_id}/revoke", response_model=APIKeyResponse)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyResponse:
    api_key = await api_key_service.get_key(db, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    revoked = await api_key_service.revoke_key(db, api_key=api_key)
    return _serialize(revoked)
