from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDService[ModelT: Base]:
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def create(self, session: AsyncSession, **values: Any) -> ModelT:
        instance = self.model(**values)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def get(self, session: AsyncSession, object_id: Any) -> ModelT | None:
        return await session.get(self.model, object_id)

    async def list(self, session: AsyncSession, limit: int = 100) -> list[ModelT]:
        query: Select[tuple[ModelT]] = select(self.model).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        instance: ModelT,
        **values: Any,
    ) -> ModelT:
        for key, value in values.items():
            setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, instance: ModelT) -> None:
        await session.delete(instance)
