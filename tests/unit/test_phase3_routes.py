import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.projects import router as projects_router
from api.v1.sessions import router as sessions_router
from core.database import get_db_session
from services.project_service import project_service
from services.project_state_service import project_state_service
from services.session_service import session_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")

    async def override_db():
        yield None

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_create_project_route() -> None:
    app = build_test_app()
    owner_id = uuid.uuid4()
    project_id = uuid.uuid4()
    mocked_project = AsyncMock()
    mocked_project.id = project_id
    mocked_project.owner_id = owner_id
    mocked_project.name = "alpha"
    mocked_project.description = "desc"
    mocked_project.local_only = False
    mocked_project.token_quota = None

    original = project_service.create_project
    project_service.create_project = AsyncMock(return_value=mocked_project)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/projects",
            json={
                "owner_id": str(owner_id),
                "name": "alpha",
                "description": "desc",
                "local_only": False,
            },
        )

    project_service.create_project = original

    assert response.status_code == 201
    assert response.json()["id"] == str(project_id)


async def test_update_project_state_route() -> None:
    app = build_test_app()
    project_id = uuid.uuid4()
    state_id = uuid.uuid4()
    mocked_state = AsyncMock()
    mocked_state.id = state_id
    mocked_state.project_id = project_id
    mocked_state.state = {"branch": "main"}

    original = project_state_service.update_state
    project_state_service.update_state = AsyncMock(return_value=mocked_state)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.put(
            f"/api/v1/projects/{project_id}/state",
            json={"state": {"branch": "main"}},
        )

    project_state_service.update_state = original

    assert response.status_code == 200
    assert response.json()["state"] == {"branch": "main"}


async def test_add_message_route() -> None:
    app = build_test_app()
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    message_id = uuid.uuid4()

    mocked_session = AsyncMock()
    mocked_session.id = session_id
    mocked_session.project_id = project_id
    mocked_session.user_id = user_id
    mocked_session.parent_session_id = None
    mocked_session.title = "Session"
    mocked_session.status = "active"

    mocked_message = AsyncMock()
    mocked_message.id = message_id
    mocked_message.session_id = session_id
    mocked_message.parent_message_id = None
    mocked_message.role = "user"
    mocked_message.content = "hello"
    mocked_message.sequence_number = 1
    mocked_message.attachments = []

    original_get = session_service.get_session
    original_add = session_service.add_message
    session_service.get_session = AsyncMock(return_value=mocked_session)
    session_service.add_message = AsyncMock(return_value=mocked_message)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/projects/{project_id}/sessions/{session_id}/messages",
            json={"role": "user", "content": "hello", "attachments": []},
        )

    session_service.get_session = original_get
    session_service.add_message = original_add

    assert response.status_code == 201
    assert response.json()["id"] == str(message_id)


async def test_branch_session_route() -> None:
    app = build_test_app()
    project_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    branch_session_id = uuid.uuid4()
    message_id = uuid.uuid4()

    mocked_session = AsyncMock()
    mocked_session.id = session_id
    mocked_session.project_id = project_id
    mocked_session.user_id = user_id
    mocked_session.parent_session_id = None
    mocked_session.title = "Session"
    mocked_session.status = "active"

    mocked_branch = AsyncMock()
    mocked_branch.id = branch_session_id
    mocked_branch.project_id = project_id
    mocked_branch.user_id = user_id
    mocked_branch.parent_session_id = session_id
    mocked_branch.title = "Branch"
    mocked_branch.status = "active"

    original_get = session_service.get_session
    original_branch = session_service.branch_session
    session_service.get_session = AsyncMock(return_value=mocked_session)
    session_service.branch_session = AsyncMock(return_value=mocked_branch)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/projects/{project_id}/sessions/{session_id}/branch",
            json={"message_id": str(message_id), "title": "Branch"},
        )

    session_service.get_session = original_get
    session_service.branch_session = original_branch

    assert response.status_code == 200
    assert response.json()["id"] == str(branch_session_id)
    assert response.json()["parent_session_id"] == str(session_id)
