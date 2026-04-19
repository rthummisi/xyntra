from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from services.prompt_service import prompt_service


async def test_create_version_increments_template_version() -> None:
    session = AsyncMock()
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="summarizer",
        version=1,
        content="v1",
        tags=["default"],
    )
    original = prompt_service.create_template
    prompt_service.create_template = AsyncMock(
        return_value=SimpleNamespace(version=2, content="v2")
    )

    try:
        created = await prompt_service.create_version(
            session,
            template=existing,
            content="v2",
        )
    finally:
        prompt_service.create_template = original

    assert created.version == 2
    assert created.content == "v2"


async def test_diff_versions_raises_when_version_missing() -> None:
    session = AsyncMock()
    template = SimpleNamespace(name="summarizer", project_id=None)
    original = prompt_service._get_version
    prompt_service._get_version = AsyncMock(return_value=None)

    try:
        try:
            await prompt_service.diff_versions(
                session,
                template=template,
                from_version=1,
                to_version=2,
            )
        except ValueError as exc:
            assert str(exc) == "Prompt template version not found."
        else:
            raise AssertionError("Expected diff_versions to fail for missing version.")
    finally:
        prompt_service._get_version = original
