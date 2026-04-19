from __future__ import annotations

import json
from pathlib import Path

from core.config import get_settings

settings = get_settings()


class ArtifactStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_text(
        self,
        *,
        project_id: str,
        artifact_name: str,
        version: int,
        content: str,
    ) -> str:
        artifact_dir = self.root / project_id / artifact_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"v{version}.txt"
        artifact_path.write_text(content, encoding="utf-8")
        return str(artifact_path)

    def save_json(
        self,
        *,
        project_id: str,
        artifact_name: str,
        version: int,
        payload: dict,
    ) -> str:
        artifact_dir = self.root / project_id / artifact_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"v{version}.json"
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(artifact_path)

    def read(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")


artifact_storage = ArtifactStorage(settings.artifacts_root)
