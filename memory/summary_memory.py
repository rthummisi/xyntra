from __future__ import annotations

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.memory_summary import MemorySummary


class SummaryMemoryStore:
    async def list_summaries(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
    ) -> list[MemorySummary]:
        result = await session.execute(
            select(MemorySummary)
            .where(MemorySummary.session_id == session_id)
            .order_by(desc(MemorySummary.created_at))
        )
        return list(result.scalars().all())

    async def create_summary(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
        content: str,
        token_count: int,
        summary_type: str = "summary",
    ) -> MemorySummary:
        summary = MemorySummary(
            session_id=session_id,
            content=content,
            token_count=token_count,
            summary_type=summary_type,
        )
        session.add(summary)
        await session.commit()
        await session.refresh(summary)
        return summary


summary_memory_store = SummaryMemoryStore()
