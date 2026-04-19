from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from services.task_service import task_service
from workers.celery_app import celery_app


async def _retry_dead_letter_entry(entry_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        assert isinstance(session, AsyncSession)
        entry = await task_service.get_dlq_entry(session, uuid.UUID(entry_id))
        if entry is None:
            raise ValueError("DLQ entry not found.")
        updated = await task_service.retry_dlq_entry(session, entry)
        return {
            "status": updated.status,
            "dead_letter_id": str(updated.id),
            "retry_count": updated.retry_count,
            "payload": updated.payload,
        }


@celery_app.task(name="xyntra.dlq.retry")
def retry_dead_letter(entry_id: str) -> dict:
    return asyncio.run(_retry_dead_letter_entry(entry_id))
