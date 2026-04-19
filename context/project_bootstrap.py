from __future__ import annotations

from context.selector import ContextChunk


def bootstrap_project_context(
    project_name: str,
    description: str | None,
) -> list[ContextChunk]:
    summary = f"Project: {project_name}"
    if description:
        summary += f"\nDescription: {description}"
    return [ContextChunk(content=summary, source="project_bootstrap", score=1.0)]
