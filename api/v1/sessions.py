from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.project_service import project_service
from services.session_service import session_service

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["sessions"])


class SessionCreateRequest(BaseModel):
    user_id: uuid.UUID
    title: str


class MessageCreateRequest(BaseModel):
    role: str
    content: str
    attachments: list[dict] = []
    parent_message_id: uuid.UUID | None = None


class BranchSessionRequest(BaseModel):
    message_id: uuid.UUID
    title: str


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    parent_session_id: uuid.UUID | None
    title: str
    status: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    parent_message_id: uuid.UUID | None
    role: str
    content: str
    sequence_number: int
    attachments: list[dict]


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    project_id: uuid.UUID,
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    project = await project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    created = await session_service.create_session(
        db,
        project_id=project_id,
        user_id=payload.user_id,
        title=payload.title,
    )
    return SessionResponse.model_validate(created)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[SessionResponse]:
    sessions = await session_service.list_sessions(db, project_id=project_id)
    return [SessionResponse.model_validate(item) for item in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    session_obj = await session_service.get_session(db, session_id)
    if session_obj is None or session_obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    return SessionResponse.model_validate(session_obj)


@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: MessageCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    session_obj = await session_service.get_session(db, session_id)
    if session_obj is None or session_obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    message = await session_service.add_message(
        db,
        session_id=session_id,
        role=payload.role,
        content=payload.content,
        attachments=payload.attachments,
        parent_message_id=payload.parent_message_id,
    )
    return MessageResponse.model_validate(message)


@router.post("/{session_id}/branch", response_model=SessionResponse)
async def branch_session(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: BranchSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    session_obj = await session_service.get_session(db, session_id)
    if session_obj is None or session_obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    branch = await session_service.branch_session(
        db,
        source_session=session_obj,
        branch_from_message_id=payload.message_id,
        title=payload.title,
    )
    return SessionResponse.model_validate(branch)


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def list_session_messages(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[MessageResponse]:
    session_obj = await session_service.get_session(db, session_id)
    if session_obj is None or session_obj.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found.")
    messages = await session_service.list_messages(db, session_id=session_id)
    return [MessageResponse.model_validate(message) for message in messages]
