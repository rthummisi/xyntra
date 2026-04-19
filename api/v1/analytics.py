from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.cost_service import cost_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


class SpendSummaryResponse(BaseModel):
    items: list[dict]


class SpendDashboardResponse(BaseModel):
    summary: dict
    by_project: list[dict]
    by_model: list[dict]
    by_date: list[dict]


class QuotaStatusResponse(BaseModel):
    allowed: bool
    consumed_tokens: int
    token_quota: int | None
    utilization: float
    threshold_reached: bool
    exceeded: bool


@router.get("/spend", response_model=SpendSummaryResponse)
async def spend_summary(
    group_by: str = "project",
    project_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    model_name: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> SpendSummaryResponse:
    items = await cost_service.summarize_spend(
        db,
        group_by=group_by,
        project_id=project_id,
        session_id=session_id,
        model_name=model_name,
        date_from=date_from,
        date_to=date_to,
    )
    return SpendSummaryResponse(items=items)


@router.get("/dashboard", response_model=SpendDashboardResponse)
async def spend_dashboard(
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> SpendDashboardResponse:
    payload = await cost_service.dashboard(db, project_id=project_id)
    return SpendDashboardResponse(**payload)


@router.get("/quota", response_model=QuotaStatusResponse)
async def quota_status(
    consumed_tokens: int,
    token_quota: int | None = None,
) -> QuotaStatusResponse:
    payload = cost_service.evaluate_quota(
        consumed_tokens=consumed_tokens,
        token_quota=token_quota,
    )
    return QuotaStatusResponse(**payload)
