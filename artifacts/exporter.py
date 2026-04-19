from __future__ import annotations

import json
import zipfile
from pathlib import Path


class ArtifactExporter:
    def export_json(self, payload: dict, output_path: str) -> str:
        path = Path(output_path)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def export_markdown(self, content: str, output_path: str) -> str:
        path = Path(output_path)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def export_zip(self, source_paths: list[str], output_path: str) -> str:
        path = Path(output_path)
        with zipfile.ZipFile(path, "w") as archive:
            for source in source_paths:
                source_path = Path(source)
                archive.write(source_path, arcname=source_path.name)
        return str(path)


artifact_exporter = ArtifactExporter()
