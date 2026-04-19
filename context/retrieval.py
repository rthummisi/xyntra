from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from context.selector import ContextChunk
from models.memory_summary import RetrievedContext


class RetrievalService:
    async def retrieve_for_project(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        limit: int = 8,
    ) -> list[ContextChunk]:
        result = await session.execute(
            select(RetrievedContext)
            .where(RetrievedContext.project_id == project_id)
            .order_by(RetrievedContext.score.desc())
            .limit(limit)
        )
        return [
            ContextChunk(
                content=item.content,
                source=item.source_type,
                score=item.score,
            )
            for item in result.scalars().all()
        ]


retrieval_service = RetrievalService()
