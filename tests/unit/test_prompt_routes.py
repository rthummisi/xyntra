from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.prompts import router as prompts_router
from core.database import get_db_session
from services.prompt_service import prompt_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(prompts_router, prefix="/api/v1")

    async def override_db():
        yield None

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_create_prompt_template_route() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mocked_template = SimpleNamespace(
        id=template_id,
        project_id=project_id,
        user_id=user_id,
        name="summarizer",
        version=1,
        content="Summarize this.",
        tags=["default"],
    )

    original = prompt_service.create_template
    prompt_service.create_template = AsyncMock(return_value=mocked_template)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/prompts",
            json={
                "project_id": str(project_id),
                "user_id": str(user_id),
                "name": "summarizer",
                "content": "Summarize this.",
                "tags": ["default"],
            },
        )

    prompt_service.create_template = original

    assert response.status_code == 201
    assert response.json()["name"] == "summarizer"


async def test_diff_prompt_template_route() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    mocked_template = SimpleNamespace(
        id=template_id,
        project_id=None,
        user_id=None,
        name="summarizer",
        version=2,
        content="v2",
        tags=["default"],
    )

    original_get = prompt_service.get_template
    original_diff = prompt_service.diff_versions
    prompt_service.get_template = AsyncMock(return_value=mocked_template)
    prompt_service.diff_versions = AsyncMock(return_value="--- old\n+++ new")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/prompts/{template_id}/diff?from_version=1&to_version=2"
        )

    prompt_service.get_template = original_get
    prompt_service.diff_versions = original_diff

    assert response.status_code == 200
    assert response.json()["diff"].startswith("--- old")


async def test_list_prompt_templates_route() -> None:
    app = build_test_app()
    template = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=None,
        user_id=None,
        name="summarizer",
        version=2,
        content="v2",
        tags=["default"],
    )

    original = prompt_service.list_templates
    prompt_service.list_templates = AsyncMock(return_value=[template])

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/prompts")

    prompt_service.list_templates = original

    assert response.status_code == 200
    assert response.json()[0]["name"] == "summarizer"


async def test_create_prompt_template_version_route() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    template = SimpleNamespace(
        id=template_id,
        project_id=None,
        user_id=None,
        name="summarizer",
        version=1,
        content="v1",
        tags=["default"],
    )
    versioned = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=None,
        user_id=None,
        name="summarizer",
        version=2,
        content="v2",
        tags=["default"],
    )

    original_get = prompt_service.get_template
    original_create_version = prompt_service.create_version
    prompt_service.get_template = AsyncMock(return_value=template)
    prompt_service.create_version = AsyncMock(return_value=versioned)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/prompts/{template_id}/versions",
            json={"content": "v2"},
        )

    prompt_service.get_template = original_get
    prompt_service.create_version = original_create_version

    assert response.status_code == 201
    assert response.json()["version"] == 2


async def test_rollback_prompt_template_route() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    template = SimpleNamespace(
        id=template_id,
        project_id=None,
        user_id=None,
        name="summarizer",
        version=3,
        content="v3",
        tags=["default"],
    )
    rolled_back = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=None,
        user_id=None,
        name="summarizer",
        version=4,
        content="v1",
        tags=["default"],
    )

    original_get = prompt_service.get_template
    original_rollback = prompt_service.rollback
    prompt_service.get_template = AsyncMock(return_value=template)
    prompt_service.rollback = AsyncMock(return_value=rolled_back)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/prompts/{template_id}/rollback?version=1"
        )

    prompt_service.get_template = original_get
    prompt_service.rollback = original_rollback

    assert response.status_code == 200
    assert response.json()["version"] == 4
    assert response.json()["content"] == "v1"


async def test_get_prompt_template_route_returns_404_when_missing() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    original = prompt_service.get_template
    prompt_service.get_template = AsyncMock(return_value=None)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/api/v1/prompts/{template_id}")

    prompt_service.get_template = original

    assert response.status_code == 404
    assert response.json()["detail"] == "Prompt template not found."


async def test_delete_prompt_template_route() -> None:
    app = build_test_app()
    template_id = uuid.uuid4()
    template = SimpleNamespace(
        id=template_id,
        project_id=None,
        user_id=None,
        name="summarizer",
        version=1,
        content="v1",
        tags=["default"],
    )
    original_get = prompt_service.get_template
    original_delete = prompt_service.delete_template
    prompt_service.get_template = AsyncMock(return_value=template)
    prompt_service.delete_template = AsyncMock(return_value=None)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.delete(f"/api/v1/prompts/{template_id}")

    prompt_service.get_template = original_get
    prompt_service.delete_template = original_delete

    assert response.status_code == 204
