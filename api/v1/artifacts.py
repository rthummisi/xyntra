from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.artifact_service import artifact_service

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactCreateRequest(BaseModel):
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    name: str
    kind: str
    content: str
    metadata_json: dict | None = None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    name: str
    kind: str
    version: int
    file_path: str
    metadata_json: dict


class ArtifactExportResponse(BaseModel):
    file_path: str


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    payload: ArtifactCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ArtifactResponse:
    artifact = await artifact_service.create_artifact(db, **payload.model_dump())
    return ArtifactResponse.model_validate(artifact)


@router.get("", response_model=list[ArtifactResponse])
async def list_artifacts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[ArtifactResponse]:
    artifacts = await artifact_service.list_artifacts(db, project_id=project_id)
    return [ArtifactResponse.model_validate(artifact) for artifact in artifacts]


@router.post("/export", response_model=ArtifactExportResponse)
async def export_artifacts(
    project_id: uuid.UUID,
    output_path: str,
    db: AsyncSession = Depends(get_db_session),
) -> ArtifactExportResponse:
    file_path = await artifact_service.export_artifact_bundle(
        db,
        project_id=project_id,
        output_path=output_path,
    )
    return ArtifactExportResponse(file_path=file_path)
