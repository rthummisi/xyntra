from __future__ import annotations

import difflib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.prompt_template import PromptTemplate


class PromptService:
    async def create_template(
        self,
        session: AsyncSession,
        *,
        name: str,
        content: str,
        project_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
    ) -> PromptTemplate:
        version = await self._next_version(
            session,
            project_id=project_id,
            name=name,
        )
        template = PromptTemplate(
            project_id=project_id,
            user_id=user_id,
            name=name,
            version=version,
            content=content,
            tags=tags or [],
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template

    async def list_templates(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None = None,
        tag: str | None = None,
        latest_only: bool = True,
    ) -> list[PromptTemplate]:
        query = select(PromptTemplate).order_by(
            PromptTemplate.name.asc(),
            PromptTemplate.version.desc(),
        )
        if project_id is not None:
            query = query.where(PromptTemplate.project_id == project_id)
        result = await session.execute(query)
        templates = list(result.scalars().all())
        if tag is not None:
            templates = [template for template in templates if tag in template.tags]
        if not latest_only:
            return templates

        latest_by_scope: dict[tuple[str, str | None], PromptTemplate] = {}
        for template in templates:
            key = (
                template.name,
                str(template.project_id) if template.project_id else None,
            )
            latest_by_scope.setdefault(key, template)
        return list(latest_by_scope.values())

    async def get_template(
        self,
        session: AsyncSession,
        template_id: uuid.UUID,
    ) -> PromptTemplate | None:
        return await session.get(PromptTemplate, template_id)

    async def create_version(
        self,
        session: AsyncSession,
        *,
        template: PromptTemplate,
        content: str,
        tags: list[str] | None = None,
    ) -> PromptTemplate:
        return await self.create_template(
            session,
            name=template.name,
            content=content,
            project_id=template.project_id,
            user_id=template.user_id,
            tags=tags if tags is not None else template.tags,
        )

    async def delete_template(
        self,
        session: AsyncSession,
        template: PromptTemplate,
    ) -> None:
        await session.delete(template)
        await session.commit()

    async def diff_versions(
        self,
        session: AsyncSession,
        *,
        template: PromptTemplate,
        from_version: int,
        to_version: int,
    ) -> str:
        source = await self._get_version(
            session,
            project_id=template.project_id,
            name=template.name,
            version=from_version,
        )
        target = await self._get_version(
            session,
            project_id=template.project_id,
            name=template.name,
            version=to_version,
        )
        if source is None or target is None:
            raise ValueError("Prompt template version not found.")

        diff = difflib.unified_diff(
            source.content.splitlines(),
            target.content.splitlines(),
            fromfile=f"{template.name}@v{from_version}",
            tofile=f"{template.name}@v{to_version}",
            lineterm="",
        )
        return "\n".join(diff)

    async def rollback(
        self,
        session: AsyncSession,
        *,
        template: PromptTemplate,
        version: int,
    ) -> PromptTemplate:
        source = await self._get_version(
            session,
            project_id=template.project_id,
            name=template.name,
            version=version,
        )
        if source is None:
            raise ValueError("Prompt template version not found.")
        return await self.create_template(
            session,
            name=source.name,
            content=source.content,
            project_id=source.project_id,
            user_id=source.user_id,
            tags=source.tags,
        )

    async def _next_version(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None,
        name: str,
    ) -> int:
        query = select(PromptTemplate).where(PromptTemplate.name == name)
        if project_id is None:
            query = query.where(PromptTemplate.project_id.is_(None))
        else:
            query = query.where(PromptTemplate.project_id == project_id)
        result = await session.execute(
            query.order_by(PromptTemplate.version.desc()).limit(1)
        )
        existing = result.scalar_one_or_none()
        return 1 if existing is None else existing.version + 1

    async def _get_version(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None,
        name: str,
        version: int,
    ) -> PromptTemplate | None:
        query = select(PromptTemplate).where(
            PromptTemplate.name == name,
            PromptTemplate.version == version,
        )
        if project_id is None:
            query = query.where(PromptTemplate.project_id.is_(None))
        else:
            query = query.where(PromptTemplate.project_id == project_id)
        result = await session.execute(query.limit(1))
        return result.scalar_one_or_none()


prompt_service = PromptService()
