from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import models  # noqa: F401
from models.base import Base
from models.project import Project
from models.session import Session
from models.user import User


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"{name} is required for integration tests.")
    return value


@pytest_asyncio.fixture
async def integration_engine() -> AsyncIterator:
    database_url = _required_env("TEST_DATABASE_URL")
    engine = create_async_engine(database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def integration_session(integration_engine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(
        bind=integration_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def integration_redis() -> AsyncIterator[Redis]:
    redis_url = _required_env("TEST_REDIS_URL")
    client = Redis.from_url(redis_url, decode_responses=True)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest_asyncio.fixture
async def seeded_project(integration_session: AsyncSession) -> Project:
    user = User(
        email=f"test-{uuid.uuid4().hex}@example.com",
        display_name="Integration User",
        is_active=True,
    )
    integration_session.add(user)
    await integration_session.flush()

    project = Project(
        owner_id=user.id,
        name="Integration Project",
        description="Integration fixture",
        local_only=False,
        token_quota=None,
    )
    integration_session.add(project)
    await integration_session.commit()
    await integration_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def seeded_session(
    integration_session: AsyncSession,
    seeded_project: Project,
) -> Session:
    project_user = await integration_session.get(User, seeded_project.owner_id)
    session = Session(
        project_id=seeded_project.id,
        user_id=project_user.id,
        title="Integration Session",
        status="active",
    )
    integration_session.add(session)
    await integration_session.commit()
    await integration_session.refresh(session)
    return session
