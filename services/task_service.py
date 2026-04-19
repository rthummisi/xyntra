from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.events import event_bus
from models.dead_letter import DeadLetterQueueEntry
from models.task import Task
from models.task_run import TaskRun
from tasks.batch_executor import batch_executor
from tasks.executor import task_executor
from tasks.planner import task_planner
from tasks.task_graph import task_graph


class TaskService:
    async def create_task(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        session_id: uuid.UUID | None,
        name: str,
        task_type: str,
        input_payload: dict,
        description: str | None = None,
    ) -> Task:
        task = Task(
            project_id=project_id,
            session_id=session_id,
            name=name,
            task_type=task_type,
            input_payload=input_payload,
            description=description,
            status="pending",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def list_tasks(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> list[Task]:
        result = await session.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_task(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
    ) -> Task | None:
        return await session.get(Task, task_id)

    async def queue_task(self, session: AsyncSession, task: Task) -> TaskRun:
        return await task_executor.queue_task(session, task)

    async def plan_and_queue(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        session_id: uuid.UUID | None,
        objective: str,
    ) -> list[Task]:
        plan = task_planner.plan(objective)
        ordered = task_graph.resolve(plan)
        created_tasks: list[Task] = []
        for planned in ordered:
            created_tasks.append(
                Task(
                    project_id=project_id,
                    session_id=session_id,
                    name=planned.name,
                    task_type=planned.task_type,
                    input_payload=planned.input_payload,
                    description=planned.description,
                    status="pending",
                )
            )
        session.add_all(created_tasks)
        await session.commit()
        for task in created_tasks:
            await session.refresh(task)
        await batch_executor.queue_many(session, created_tasks)
        return created_tasks

    async def push_to_dlq(
        self,
        session: AsyncSession,
        *,
        task_name: str,
        payload: dict,
        error_message: str,
    ) -> DeadLetterQueueEntry:
        entry = DeadLetterQueueEntry(
            task_name=task_name,
            payload=payload,
            error_history=[{"error": error_message}],
            retry_count=0,
            status="failed",
            last_error=error_message,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        await event_bus.emit(
            session,
            event_type="task.failed",
            payload={
                "task_name": task_name,
                "payload": payload,
                "error_message": error_message,
                "dead_letter_id": str(entry.id),
            },
        )
        return entry

    async def list_dlq(self, session: AsyncSession) -> list[DeadLetterQueueEntry]:
        result = await session.execute(
            select(DeadLetterQueueEntry).order_by(
                DeadLetterQueueEntry.created_at.desc()
            )
        )
        return list(result.scalars().all())

    async def get_dlq_entry(
        self,
        session: AsyncSession,
        entry_id: uuid.UUID,
    ) -> DeadLetterQueueEntry | None:
        return await session.get(DeadLetterQueueEntry, entry_id)

    async def retry_dlq_entry(
        self,
        session: AsyncSession,
        entry: DeadLetterQueueEntry,
    ) -> DeadLetterQueueEntry:
        task_run_id: str | None = None
        task_id = entry.payload.get("task_id")
        if task_id is not None:
            task = await self.get_task(session, uuid.UUID(str(task_id)))
            if task is not None:
                task_run = await task_executor.requeue_failed(session, task)
                task_run_id = str(task_run.id)
        entry.retry_count += 1
        entry.status = "requeued"
        history = list(entry.error_history)
        history.append(
            {
                "action": "retry",
                "task_run_id": task_run_id,
            }
        )
        entry.error_history = history
        await session.commit()
        await session.refresh(entry)
        return entry

    async def discard_dlq_entry(
        self,
        session: AsyncSession,
        entry: DeadLetterQueueEntry,
    ) -> DeadLetterQueueEntry:
        entry.status = "discarded"
        await session.commit()
        await session.refresh(entry)
        return entry


task_service = TaskService()
