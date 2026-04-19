from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreateRequest(BaseModel):
    project_id: uuid.UUID
    session_id: uuid.UUID | None = None
    name: str
    task_type: str
    input_payload: dict
    description: str | None = None


class TaskPlanRequest(BaseModel):
    project_id: uuid.UUID
    session_id: uuid.UUID | None = None
    objective: str


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    session_id: uuid.UUID | None
    name: str
    task_type: str
    status: str
    input_payload: dict
    description: str | None


class TaskRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    status: str
    attempt_number: int
    output_payload: dict
    error_message: str | None


class DeadLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_name: str
    payload: dict
    error_history: list[dict]
    retry_count: int
    status: str
    last_error: str | None


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await task_service.create_task(db, **payload.model_dump())
    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[TaskResponse]:
    tasks = await task_service.list_tasks(db, project_id=project_id)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post(
    "/plan",
    response_model=list[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def plan_tasks(
    payload: TaskPlanRequest,
    db: AsyncSession = Depends(get_db_session),
) -> list[TaskResponse]:
    tasks = await task_service.plan_and_queue(
        db,
        project_id=payload.project_id,
        session_id=payload.session_id,
        objective=payload.objective,
    )
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post("/{task_id}/queue", response_model=TaskRunResponse)
async def queue_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> TaskRunResponse:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    task_run = await task_service.queue_task(db, task)
    return TaskRunResponse.model_validate(task_run)


@router.get("/dlq", response_model=list[DeadLetterResponse])
async def list_dead_letter_queue(
    db: AsyncSession = Depends(get_db_session),
) -> list[DeadLetterResponse]:
    entries = await task_service.list_dlq(db)
    return [DeadLetterResponse.model_validate(entry) for entry in entries]


@router.get("/dlq/{entry_id}", response_model=DeadLetterResponse)
async def get_dead_letter_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DeadLetterResponse:
    entry = await task_service.get_dlq_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="DLQ entry not found.")
    return DeadLetterResponse.model_validate(entry)


@router.post("/dlq/{entry_id}/retry", response_model=DeadLetterResponse)
async def retry_dead_letter_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DeadLetterResponse:
    entry = await task_service.get_dlq_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="DLQ entry not found.")
    updated = await task_service.retry_dlq_entry(db, entry)
    return DeadLetterResponse.model_validate(updated)


@router.post("/dlq/{entry_id}/discard", response_model=DeadLetterResponse)
async def discard_dead_letter_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DeadLetterResponse:
    entry = await task_service.get_dlq_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="DLQ entry not found.")
    updated = await task_service.discard_dlq_entry(db, entry)
    return DeadLetterResponse.model_validate(updated)
