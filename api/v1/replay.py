from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.replay_service import replay_service

router = APIRouter(prefix="/replay", tags=["replay"])


class ReplayResponse(BaseModel):
    payload: dict


@router.get("/{task_run_id}", response_model=ReplayResponse)
async def replay_task_run(
    task_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ReplayResponse:
    try:
        payload = await replay_service.replay_task_run(db, task_run_id=task_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplayResponse(payload=payload)
