from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval


class ApprovalService:
    async def create_pending(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None,
        task_id: uuid.UUID | None,
        reason: str,
    ) -> Approval:
        approval = Approval(
            project_id=project_id,
            task_id=task_id,
            status="pending",
            reason=reason,
        )
        session.add(approval)
        await session.commit()
        await session.refresh(approval)
        return approval

    async def list_pending(self, session: AsyncSession) -> list[Approval]:
        result = await session.execute(
            select(Approval).where(Approval.status == "pending")
        )
        return list(result.scalars().all())

    async def resolve(
        self,
        session: AsyncSession,
        *,
        approval_id: uuid.UUID,
        status: str,
        approver_identifier: str,
    ) -> Approval | None:
        approval = await session.get(Approval, approval_id)
        if approval is None:
            return None
        approval.status = status
        approval.approver_identifier = approver_identifier
        await session.commit()
        await session.refresh(approval)
        return approval


approval_service = ApprovalService()
