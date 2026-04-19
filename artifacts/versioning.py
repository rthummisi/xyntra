from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from artifacts.diff_manager import diff_manager
from artifacts.storage import artifact_storage
from models.artifact import Artifact


class ArtifactVersioningService:
    async def save_version(
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
        result = await session.execute(
            select(func.coalesce(func.max(Artifact.version), 0)).where(
                Artifact.project_id == project_id,
                Artifact.name == name,
            )
        )
        next_version = int(result.scalar_one()) + 1
        file_path = artifact_storage.save_text(
            project_id=str(project_id),
            artifact_name=name,
            version=next_version,
            content=content,
        )
        artifact = Artifact(
            project_id=project_id,
            task_id=task_id,
            name=name,
            kind=kind,
            version=next_version,
            file_path=file_path,
            metadata_json=metadata_json or {},
        )
        session.add(artifact)
        await session.commit()
        await session.refresh(artifact)
        return artifact

    async def diff_latest(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        name: str,
    ) -> str:
        result = await session.execute(
            select(Artifact)
            .where(Artifact.project_id == project_id, Artifact.name == name)
            .order_by(Artifact.version.desc())
            .limit(2)
        )
        artifacts = list(result.scalars().all())
        if len(artifacts) < 2:
            return ""
        current = artifact_storage.read(artifacts[0].file_path)
        previous = artifact_storage.read(artifacts[1].file_path)
        return diff_manager.diff(previous, current)


artifact_versioning_service = ArtifactVersioningService()
