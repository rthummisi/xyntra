from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.context_service import ContextInspection, context_service

router = APIRouter(prefix="/context", tags=["context"])


class ContextInspectionResponse(ContextInspection):
    pass


@router.get("/inspect", response_model=ContextInspectionResponse)
async def inspect_context(
    project_id: uuid.UUID,
    model_name: str | None = None,
    total_window: int | None = None,
    limit: int = 8,
    db: AsyncSession = Depends(get_db_session),
) -> ContextInspectionResponse:
    inspection = await context_service.inspect(
        db,
        project_id=project_id,
        model_name=model_name,
        total_window=total_window,
        limit=limit,
    )
    return ContextInspectionResponse(**inspection.model_dump())
