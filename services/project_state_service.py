from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.project_state import ProjectState


class ProjectStateService:
    async def get_state(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> ProjectState | None:
        result = await session.execute(
            select(ProjectState).where(ProjectState.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_state(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        state: dict,
    ) -> ProjectState:
        project_state = await self.get_state(session, project_id)
        if project_state is None:
            project_state = ProjectState(project_id=project_id, state=state)
            session.add(project_state)
        else:
            project_state.state = state

        await session.commit()
        await session.refresh(project_state)
        return project_state


project_state_service = ProjectStateService()
