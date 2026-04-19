from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task
from tasks.executor import task_executor


class BatchExecutor:
    async def queue_many(
        self,
        session: AsyncSession,
        tasks: list[Task],
    ) -> list[str]:
        queued_ids: list[str] = []
        for task in tasks:
            task_run = await task_executor.queue_task(session, task)
            queued_ids.append(str(task_run.id))
        return queued_ids


batch_executor = BatchExecutor()
