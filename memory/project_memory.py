from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.decision import Decision
from models.project_state import ProjectState


class ProjectMemoryStore:
    async def fetch_project_state(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> ProjectState | None:
        result = await session.execute(
            select(ProjectState).where(ProjectState.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_decisions(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> list[Decision]:
        result = await session.execute(
            select(Decision).where(Decision.project_id == project_id)
        )
        return list(result.scalars().all())


project_memory_store = ProjectMemoryStore()
