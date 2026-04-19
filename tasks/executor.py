from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.events import event_bus
from models.task import Task
from models.task_run import TaskRun
from tasks.state_machine import task_state_machine


class TaskExecutor:
    async def queue_task(self, session: AsyncSession, task: Task) -> TaskRun:
        task.status = task_state_machine.transition(task.status, "queued")
        task_run = TaskRun(task_id=task.id, status="queued", attempt_number=1)
        session.add(task_run)
        await session.commit()
        await session.refresh(task_run)
        return task_run

    async def start_run(
        self,
        session: AsyncSession,
        task: Task,
        task_run: TaskRun,
    ) -> None:
        task.status = task_state_machine.transition(task.status, "running")
        task_run.status = "running"
        await session.commit()

    async def complete_run(
        self,
        session: AsyncSession,
        *,
        task: Task,
        task_run: TaskRun,
        output_payload: dict,
    ) -> TaskRun:
        task.status = task_state_machine.transition(task.status, "completed")
        task_run.status = "completed"
        task_run.output_payload = output_payload
        await session.commit()
        await session.refresh(task_run)
        await event_bus.emit(
            session,
            event_type="task.completed",
            payload={
                "task_id": str(task.id),
                "task_run_id": str(task_run.id),
                "project_id": str(task.project_id),
                "session_id": None if task.session_id is None else str(task.session_id),
                "output_payload": output_payload,
            },
        )
        return task_run

    async def fail_run(
        self,
        session: AsyncSession,
        *,
        task: Task,
        task_run: TaskRun,
        error_message: str,
    ) -> TaskRun:
        task.status = task_state_machine.transition(task.status, "failed")
        task_run.status = "failed"
        task_run.error_message = error_message
        await session.commit()
        await session.refresh(task_run)
        await event_bus.emit(
            session,
            event_type="task.failed",
            payload={
                "task_id": str(task.id),
                "task_run_id": str(task_run.id),
                "project_id": str(task.project_id),
                "session_id": None if task.session_id is None else str(task.session_id),
                "error_message": error_message,
            },
        )
        return task_run

    async def requeue_failed(self, session: AsyncSession, task: Task) -> TaskRun:
        task.status = task_state_machine.transition(task.status, "queued")
        task_run = TaskRun(task_id=task.id, status="queued", attempt_number=1)
        session.add(task_run)
        await session.commit()
        await session.refresh(task_run)
        return task_run

    @staticmethod
    def new_task_payload(task_id: uuid.UUID) -> dict:
        return {"task_id": str(task_id)}


task_executor = TaskExecutor()
