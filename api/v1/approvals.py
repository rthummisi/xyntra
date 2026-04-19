from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.approval import Approval
from services.approval_service import approval_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalCreateRequest(BaseModel):
    project_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    reason: str


class ApprovalResolveRequest(BaseModel):
    status: str
    approver_identifier: str


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    task_id: uuid.UUID | None
    status: str
    reason: str | None
    approver_identifier: str | None


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval(
    payload: ApprovalCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalResponse:
    approval = await approval_service.create_pending(db, **payload.model_dump())
    return ApprovalResponse.model_validate(approval)


@router.get("", response_model=list[ApprovalResponse])
async def list_approvals(
    status: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[ApprovalResponse]:
    if status == "pending":
        approvals = await approval_service.list_pending(db)
    else:
        result = await db.execute(select(Approval).order_by(Approval.created_at.desc()))
        approvals = list(result.scalars().all())
    return [ApprovalResponse.model_validate(item) for item in approvals]


@router.post("/{approval_id}/resolve", response_model=ApprovalResponse)
async def resolve_approval(
    approval_id: uuid.UUID,
    payload: ApprovalResolveRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalResponse:
    resolved = await approval_service.resolve(
        db,
        approval_id=approval_id,
        status=payload.status,
        approver_identifier=payload.approver_identifier,
    )
    if resolved is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    return ApprovalResponse.model_validate(resolved)
