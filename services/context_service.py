from __future__ import annotations

import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from context.assembler import AssembledContext, context_assembler
from context.retrieval import retrieval_service
from providers.capability_registry import capability_registry


class ContextInspection(BaseModel):
    assembled: AssembledContext
    source_project_id: uuid.UUID
    model_name: str | None = None
    total_window: int


class ContextService:
    async def inspect(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        model_name: str | None = None,
        total_window: int | None = None,
        limit: int = 8,
    ) -> ContextInspection:
        chunks = await retrieval_service.retrieve_for_project(
            session,
            project_id=project_id,
            limit=limit,
        )
        resolved_window = total_window or self._resolve_window(model_name)
        assembled = context_assembler.assemble(
            chunks=chunks,
            total_window=resolved_window,
        )
        return ContextInspection(
            assembled=assembled,
            source_project_id=project_id,
            model_name=model_name,
            total_window=resolved_window,
        )

    @staticmethod
    def _resolve_window(model_name: str | None) -> int:
        if model_name:
            if ":" in model_name:
                provider_name, provider_model = model_name.split(":", 1)
                capability = capability_registry.get(provider_name, provider_model)
                if capability is not None:
                    return capability.context_window
            for capability in capability_registry.list():
                if capability.model == model_name:
                    return capability.context_window
        return 8192


context_service = ContextService()
