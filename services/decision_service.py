from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.decision import Decision


class DecisionService:
    async def create_decision(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        decision_type: str,
        summary: str,
        rationale: str | None = None,
        metadata_json: dict | None = None,
    ) -> Decision:
        decision = Decision(
            project_id=project_id,
            decision_type=decision_type,
            summary=summary,
            rationale=rationale,
            metadata_json=metadata_json or {},
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)
        return decision

    async def list_decisions(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> list[Decision]:
        result = await session.execute(
            select(Decision)
            .where(Decision.project_id == project_id)
            .order_by(Decision.created_at.desc())
        )
        return list(result.scalars().all())


decision_service = DecisionService()
