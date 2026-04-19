from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.project_service import project_service
from services.project_state_service import project_state_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreateRequest(BaseModel):
    owner_id: uuid.UUID
    name: str
    description: str | None = None
    local_only: bool = False
    token_quota: int | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    local_only: bool | None = None
    token_quota: int | None = None


class ProjectStateUpdateRequest(BaseModel):
    state: dict


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    local_only: bool
    token_quota: int | None


class ProjectStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    state: dict


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await project_service.create_project(db, **payload.model_dump())
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    owner_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[ProjectResponse]:
    projects = await project_service.list_projects(db, owner_id=owner_id)
    return [ProjectResponse.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    updated = await project_service.update_project(
        db,
        project,
        **payload.model_dump(exclude_unset=True),
    )
    return ProjectResponse.model_validate(updated)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    project = await project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    await project_service.delete_project(db, project)


@router.get("/{project_id}/state", response_model=ProjectStateResponse)
async def get_project_state(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectStateResponse:
    project_state = await project_state_service.get_state(db, project_id)
    if project_state is None:
        raise HTTPException(status_code=404, detail="Project state not found.")
    return ProjectStateResponse.model_validate(project_state)


@router.put("/{project_id}/state", response_model=ProjectStateResponse)
async def update_project_state(
    project_id: uuid.UUID,
    payload: ProjectStateUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ProjectStateResponse:
    project_state = await project_state_service.update_state(
        db,
        project_id=project_id,
        state=payload.state,
    )
    return ProjectStateResponse.model_validate(project_state)
