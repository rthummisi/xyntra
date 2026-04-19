from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import models  # noqa: F401
from core.database import get_db_session
from main import app
from models.base import Base
from models.user import User


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"{name} is required for e2e tests.")
    return value


@pytest_asyncio.fixture
async def e2e_engine() -> AsyncIterator:
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
async def e2e_session(e2e_engine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(
        bind=e2e_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seeded_owner(e2e_session: AsyncSession) -> User:
    user = User(
        email=f"e2e-{uuid.uuid4().hex}@example.com",
        display_name="E2E Owner",
        is_active=True,
    )
    e2e_session.add(user)
    await e2e_session.commit()
    await e2e_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def e2e_client(e2e_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_db() -> AsyncIterator[AsyncSession]:
        yield e2e_session

    app.dependency_overrides[get_db_session] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()
