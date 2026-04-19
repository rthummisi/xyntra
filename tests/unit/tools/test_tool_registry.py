from __future__ import annotations

from providers.tool_registry import ToolDefinitionSchema, ToolRegistry


def test_tool_registry_registers_and_lists_tools() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinitionSchema(
            name="search",
            description="Searches indexed project content.",
            parameters={"type": "object"},
        )
    )
    registry.register(
        ToolDefinitionSchema(
            name="diff",
            description="Returns a diff for an artifact version.",
        )
    )

    tools = registry.list()

    assert len(tools) == 2
    assert {tool.name for tool in tools} == {"search", "diff"}


def test_tool_registry_overwrites_existing_definition_by_name() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinitionSchema(
            name="search",
            description="Old description",
        )
    )
    registry.register(
        ToolDefinitionSchema(
            name="search",
            description="Updated description",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        )
    )

    tool = registry.get("search")

    assert tool is not None
    assert tool.description == "Updated description"
    assert tool.parameters["type"] == "object"
