from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.project import Project
from models.project_state import ProjectState


class ProjectService:
    async def create_project(
        self,
        session: AsyncSession,
        *,
        owner_id: uuid.UUID,
        name: str,
        description: str | None = None,
        local_only: bool = False,
        token_quota: int | None = None,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            name=name,
            description=description,
            local_only=local_only,
            token_quota=token_quota,
        )
        session.add(project)
        await session.flush()

        project_state = ProjectState(project_id=project.id, state={})
        session.add(project_state)

        await session.commit()
        await session.refresh(project)
        return project

    async def get_project(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> Project | None:
        return await session.get(Project, project_id)

    async def list_projects(
        self,
        session: AsyncSession,
        *,
        owner_id: uuid.UUID | None = None,
    ) -> list[Project]:
        query = select(Project)
        if owner_id is not None:
            query = query.where(Project.owner_id == owner_id)
        result = await session.execute(query.order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    async def update_project(
        self,
        session: AsyncSession,
        project: Project,
        *,
        name: str | None = None,
        description: str | None = None,
        local_only: bool | None = None,
        token_quota: int | None = None,
    ) -> Project:
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if local_only is not None:
            project.local_only = local_only
        if token_quota is not None:
            project.token_quota = token_quota

        await session.commit()
        await session.refresh(project)
        return project

    async def delete_project(self, session: AsyncSession, project: Project) -> None:
        await session.delete(project)
        await session.commit()


project_service = ProjectService()
