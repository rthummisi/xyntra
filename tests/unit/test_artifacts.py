from artifacts.diff_manager import diff_manager
from artifacts.exporter import artifact_exporter


def test_diff_manager_produces_unified_diff() -> None:
    diff = diff_manager.diff("a\nb", "a\nc")
    assert "--- previous" in diff
    assert "+c" in diff


def test_artifact_exporter_writes_markdown(tmp_path) -> None:
    output_path = tmp_path / "artifact.md"
    written = artifact_exporter.export_markdown("# Artifact", str(output_path))
    assert written.endswith("artifact.md")
    assert output_path.read_text(encoding="utf-8") == "# Artifact"
