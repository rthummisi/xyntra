from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import APIKeyRecord, api_key_manager
from models import APIKey


class APIKeyService:
    async def create_key(
        self,
        session: AsyncSession,
        *,
        name: str,
        ttl_days: int = 90,
    ) -> tuple[str, APIKey]:
        raw_token, record = api_key_manager.create_key(ttl_days=ttl_days)
        api_key = APIKey(
            key_id=record.key_id,
            name=name,
            token_preview=record.token_preview,
            token_hash=record.token_hash,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
            last_used_at=None,
        )
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)
        return raw_token, api_key

    async def list_keys(self, session: AsyncSession) -> list[APIKey]:
        result = await session.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        return list(result.scalars().all())

    async def get_key(self, session: AsyncSession, key_id: uuid.UUID) -> APIKey | None:
        return await session.get(APIKey, key_id)

    async def rotate_key(
        self,
        session: AsyncSession,
        *,
        api_key: APIKey,
        ttl_days: int = 90,
    ) -> tuple[str, APIKey]:
        current = self._record_from_model(api_key)
        raw_token, rotated = api_key_manager.rotate_key(current, ttl_days=ttl_days)
        api_key.token_preview = rotated.token_preview
        api_key.token_hash = rotated.token_hash
        api_key.issued_at = rotated.issued_at
        api_key.expires_at = rotated.expires_at
        api_key.revoked_at = None
        api_key.last_used_at = None
        await session.commit()
        await session.refresh(api_key)
        return raw_token, api_key

    async def revoke_key(self, session: AsyncSession, *, api_key: APIKey) -> APIKey:
        api_key.revoked_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(api_key)
        return api_key

    async def touch_key(self, session: AsyncSession, *, api_key: APIKey) -> APIKey:
        api_key.last_used_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(api_key)
        return api_key

    @staticmethod
    def _record_from_model(api_key: APIKey) -> APIKeyRecord:
        return APIKeyRecord(
            key_id=api_key.key_id,
            token_preview=api_key.token_preview,
            token_hash=api_key.token_hash,
            issued_at=api_key.issued_at,
            expires_at=api_key.expires_at,
            revoked_at=api_key.revoked_at,
        )


api_key_service = APIKeyService()
