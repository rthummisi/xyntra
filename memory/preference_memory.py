from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.prompt_template import PromptTemplate


class PreferenceMemoryStore:
    async def list_user_preferences(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
    ) -> list[PromptTemplate]:
        result = await session.execute(
            select(PromptTemplate).where(PromptTemplate.user_id == user_id)
        )
        return list(result.scalars().all())


preference_memory_store = PreferenceMemoryStore()
