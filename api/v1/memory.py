from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.memory_service import MemorySnapshot, memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


class MemorySnapshotResponse(MemorySnapshot):
    pass


@router.get("/snapshot", response_model=MemorySnapshotResponse)
async def get_memory_snapshot(
    session_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> MemorySnapshotResponse:
    snapshot = await memory_service.snapshot(
        db,
        session_id=session_id,
        project_id=project_id,
        user_id=user_id,
    )
    return MemorySnapshotResponse(**snapshot.model_dump())
