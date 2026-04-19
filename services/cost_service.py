from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.spend_record import SpendRecord


class CostService:
    async def record_spend(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        task_id: uuid.UUID | None,
        provider_name: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> SpendRecord:
        record = SpendRecord(
            project_id=project_id,
            session_id=session_id,
            task_id=task_id,
            provider_name=provider_name,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def summarize_by_project(self, session: AsyncSession) -> list[dict]:
        result = await session.execute(select(SpendRecord))
        grouped: dict[str, float] = defaultdict(float)
        for record in result.scalars().all():
            grouped[str(record.project_id)] += record.cost_usd
        return [
            {"project_id": project_id, "cost_usd": cost}
            for project_id, cost in grouped.items()
        ]

    async def summarize_spend(
        self,
        session: AsyncSession,
        *,
        group_by: str = "project",
        project_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        model_name: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        result = await session.execute(select(SpendRecord))
        records = list(result.scalars().all())
        records = [
            record
            for record in records
            if self._matches_filters(
                record,
                project_id=project_id,
                session_id=session_id,
                model_name=model_name,
                date_from=date_from,
                date_to=date_to,
            )
        ]
        grouped: dict[str, dict] = {}
        for record in records:
            key = self._group_key(record, group_by=group_by)
            bucket = grouped.setdefault(
                key,
                {
                    "group": key,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "calls": 0,
                },
            )
            bucket["cost_usd"] += record.cost_usd
            bucket["input_tokens"] += record.input_tokens
            bucket["output_tokens"] += record.output_tokens
            bucket["calls"] += 1
        return [
            {
                **bucket,
                "cost_usd": round(bucket["cost_usd"], 6),
            }
            for bucket in grouped.values()
        ]

    async def dashboard(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None = None,
    ) -> dict:
        grouped_by_project = await self.summarize_spend(
            session,
            group_by="project",
            project_id=project_id,
        )
        grouped_by_model = await self.summarize_spend(
            session,
            group_by="model",
            project_id=project_id,
        )
        grouped_by_day = await self.summarize_spend(
            session,
            group_by="date",
            project_id=project_id,
        )
        total_cost = round(sum(item["cost_usd"] for item in grouped_by_project), 6)
        total_calls = sum(item["calls"] for item in grouped_by_project)
        return {
            "summary": {
                "total_cost_usd": total_cost,
                "total_calls": total_calls,
            },
            "by_project": grouped_by_project,
            "by_model": grouped_by_model,
            "by_date": grouped_by_day,
        }

    def evaluate_quota(
        self,
        *,
        consumed_tokens: int,
        token_quota: int | None,
    ) -> dict:
        if token_quota is None:
            return {
                "allowed": True,
                "consumed_tokens": consumed_tokens,
                "token_quota": None,
                "utilization": 0.0,
                "threshold_reached": False,
                "exceeded": False,
            }
        utilization = 0.0 if token_quota == 0 else consumed_tokens / token_quota
        return {
            "allowed": consumed_tokens <= token_quota,
            "consumed_tokens": consumed_tokens,
            "token_quota": token_quota,
            "utilization": round(utilization, 4),
            "threshold_reached": utilization >= 0.8,
            "exceeded": consumed_tokens > token_quota,
        }

    @staticmethod
    def _matches_filters(
        record: SpendRecord,
        *,
        project_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        model_name: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bool:
        if project_id is not None and record.project_id != project_id:
            return False
        if session_id is not None and record.session_id != session_id:
            return False
        if model_name is not None and record.model_name != model_name:
            return False
        recorded_date = CostService._normalize_date(record.recorded_at)
        if date_from is not None and recorded_date < date_from:
            return False
        if date_to is not None and recorded_date > date_to:
            return False
        return True

    @staticmethod
    def _group_key(record: SpendRecord, *, group_by: str) -> str:
        if group_by == "project":
            return str(record.project_id)
        if group_by == "session":
            return str(record.session_id)
        if group_by == "model":
            return record.model_name
        if group_by == "date":
            return CostService._normalize_date(record.recorded_at).isoformat()
        raise ValueError(f"Unsupported group_by: {group_by}")

    @staticmethod
    def _normalize_date(value: datetime | date) -> date:
        return value.date() if isinstance(value, datetime) else value


cost_service = CostService()
