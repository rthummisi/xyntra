from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.session import Session
from models.user import User
from services.project_service import project_service
from services.project_state_service import project_state_service
from services.session_service import session_service

router = APIRouter(prefix="/cli", tags=["cli"])

DEFAULT_USER_EMAIL = "cli@xyntra.local"
DEFAULT_USER_NAME = "Xyntra CLI"


class EnsureContextRequest(BaseModel):
    cwd: str
    repo_root: str | None = None
    branch: str | None = None
    project_name: str
    local_only: bool = True
    project_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None


class EnsureContextResponse(BaseModel):
    cwd: str
    repo_root: str | None = None
    branch: str | None = None
    user_id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    session_id: uuid.UUID
    local_only: bool


@router.post("/context/ensure", response_model=EnsureContextResponse)
async def ensure_cli_context(
    payload: EnsureContextRequest,
    db: AsyncSession = Depends(get_db_session),
) -> EnsureContextResponse:
    user = await _ensure_cli_user(db)

    project = None
    if payload.project_id is not None:
        project = await project_service.get_project(db, payload.project_id)
    if project is None:
        project = await project_service.create_project(
            db,
            owner_id=user.id,
            name=payload.project_name,
            description=f"CLI context for {payload.repo_root or payload.cwd}",
            local_only=payload.local_only,
        )

    session_obj = None
    if payload.session_id is not None:
        session_obj = await session_service.get_session(db, payload.session_id)
    if session_obj is None or session_obj.project_id != project.id:
        session_obj = await session_service.create_session(
            db,
            project_id=project.id,
            user_id=user.id,
            title=f"CLI session for {project.name}",
        )

    existing_state = await project_state_service.get_state(db, project.id)
    next_state = {} if existing_state is None else dict(existing_state.state)
    next_state["cli_context"] = {
        "cwd": payload.cwd,
        "repo_root": payload.repo_root,
        "branch": payload.branch,
        "project_name": payload.project_name,
    }
    await project_state_service.update_state(
        db,
        project_id=project.id,
        state=next_state,
    )

    return EnsureContextResponse(
        cwd=payload.cwd,
        repo_root=payload.repo_root,
        branch=payload.branch,
        user_id=user.id,
        project_id=project.id,
        project_name=project.name,
        session_id=session_obj.id,
        local_only=project.local_only,
    )


async def _ensure_cli_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == DEFAULT_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        email=DEFAULT_USER_EMAIL,
        display_name=DEFAULT_USER_NAME,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
