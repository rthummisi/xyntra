from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.message import Message


class SessionMemoryStore:
    async def fetch_messages(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
    ) -> list[Message]:
        result = await session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence_number.asc())
        )
        return list(result.scalars().all())


session_memory_store = SessionMemoryStore()
