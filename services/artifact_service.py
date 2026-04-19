from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from artifacts.exporter import artifact_exporter
from artifacts.versioning import artifact_versioning_service
from core.events import event_bus
from models.artifact import Artifact


class ArtifactService:
    async def create_artifact(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        task_id: uuid.UUID | None,
        name: str,
        kind: str,
        content: str,
        metadata_json: dict | None = None,
    ) -> Artifact:
        artifact = await artifact_versioning_service.save_version(
            session,
            project_id=project_id,
            task_id=task_id,
            name=name,
            kind=kind,
            content=content,
            metadata_json=metadata_json,
        )
        await event_bus.emit(
            session,
            event_type="artifact.created",
            payload={
                "artifact_id": str(artifact.id),
                "project_id": str(artifact.project_id),
                "task_id": None if artifact.task_id is None else str(artifact.task_id),
                "name": artifact.name,
                "kind": artifact.kind,
                "version": artifact.version,
                "file_path": artifact.file_path,
            },
        )
        return artifact

    async def list_artifacts(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> list[Artifact]:
        result = await session.execute(
            select(Artifact)
            .where(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
        )
        return list(result.scalars().all())

    async def export_artifact_bundle(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        output_path: str,
    ) -> str:
        artifacts = await self.list_artifacts(session, project_id=project_id)
        return artifact_exporter.export_zip(
            [artifact.file_path for artifact in artifacts],
            output_path,
        )


artifact_service = ArtifactService()
