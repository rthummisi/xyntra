from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.telemetry import telemetry_recorder
from models.provider_call import ProviderCall
from models.task import Task
from models.task_run import TaskRun


class ReplayService:
    async def replay_task_run(
        self,
        session: AsyncSession,
        *,
        task_run_id: uuid.UUID,
    ) -> dict:
        task_run = await session.get(TaskRun, task_run_id)
        if task_run is None:
            raise ValueError("Task run not found.")
        task = await session.get(Task, task_run.task_id)
        provider_calls = await session.execute(
            select(ProviderCall).where(ProviderCall.task_run_id == task_run_id)
        )
        return {
            "task": (
                None
                if task is None
                else {
                    "id": str(task.id),
                    "project_id": str(task.project_id),
                    "session_id": (
                        None if task.session_id is None else str(task.session_id)
                    ),
                    "name": task.name,
                    "task_type": task.task_type,
                    "status": task.status,
                    "input_payload": task.input_payload,
                    "description": task.description,
                }
            ),
            "task_run": {
                "id": str(task_run.id),
                "task_id": str(task_run.task_id),
                "status": task_run.status,
                "attempt_number": task_run.attempt_number,
                "worker_name": task_run.worker_name,
                "error_message": task_run.error_message,
                "output_payload": task_run.output_payload,
            },
            "provider_calls": [
                {
                    "id": str(call.id),
                    "project_id": (
                        None if call.project_id is None else str(call.project_id)
                    ),
                    "session_id": (
                        None if call.session_id is None else str(call.session_id)
                    ),
                    "task_run_id": (
                        None if call.task_run_id is None else str(call.task_run_id)
                    ),
                    "provider_name": call.provider_name,
                    "model_name": call.model_name,
                    "request_payload": call.request_payload,
                    "response_payload": call.response_payload,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "cost_usd": call.cost_usd,
                    "cache_hit": call.cache_hit,
                    "error_message": call.error_message,
                }
                for call in provider_calls.scalars().all()
            ],
            "telemetry": telemetry_recorder.export(),
        }


replay_service = ReplayService()
