from __future__ import annotations

from pydantic import BaseModel, Field


class ToolDefinitionSchema(BaseModel):
    name: str
    description: str
    parameters: dict = Field(default_factory=dict)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinitionSchema] = {}

    def register(self, tool: ToolDefinitionSchema) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinitionSchema | None:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinitionSchema]:
        return list(self._tools.values())


tool_registry = ToolRegistry()
