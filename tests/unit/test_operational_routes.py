from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.approvals import router as approvals_router
from api.v1.cache import router as cache_router
from api.v1.context import router as context_router
from api.v1.memory import router as memory_router
from api.v1.policies import router as policies_router
from api.v1.security import router as security_router
from core.database import get_db_session
from services.api_key_service import api_key_service
from services.approval_service import approval_service
from services.context_service import context_service
from services.memory_service import memory_service
from services.policy_rule_service import policy_rule_service


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(context_router, prefix="/api/v1")
    app.include_router(approvals_router, prefix="/api/v1")
    app.include_router(policies_router, prefix="/api/v1")
    app.include_router(cache_router, prefix="/api/v1")
    app.include_router(security_router, prefix="/api/v1")

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db_session] = override_db
    return app


async def test_memory_snapshot_route() -> None:
    app = build_test_app()
    original = memory_service.snapshot
    memory_service.snapshot = AsyncMock(
        return_value=SimpleNamespace(
            model_dump=lambda: {
                "session_messages": [{"id": "1", "content": "hello"}],
                "session_summaries": [],
                "project_state": {"status": "active"},
                "project_decisions": [],
                "user_preferences": [],
            }
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/memory/snapshot",
            params={
                "session_id": str(uuid.uuid4()),
                "project_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
            },
        )

    memory_service.snapshot = original

    assert response.status_code == 200
    assert response.json()["project_state"]["status"] == "active"


async def test_context_inspection_route() -> None:
    app = build_test_app()
    original = context_service.inspect
    context_service.inspect = AsyncMock(
        return_value=SimpleNamespace(
            model_dump=lambda: {
                "assembled": {
                    "chunks": [{"content": "ctx", "source": "project", "score": 0.9}],
                    "budget": {
                        "total": 8192,
                        "reserved_for_output": 2048,
                        "available_for_context": 6144,
                    },
                },
                "source_project_id": str(uuid.uuid4()),
                "model_name": "llama3.2:1b",
                "total_window": 8192,
            }
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/context/inspect",
            params={"project_id": str(uuid.uuid4()), "model_name": "llama3.2:1b"},
        )

    context_service.inspect = original

    assert response.status_code == 200
    assert response.json()["assembled"]["budget"]["available_for_context"] == 6144


async def test_approval_routes() -> None:
    app = build_test_app()
    approval_id = uuid.uuid4()
    original_create = approval_service.create_pending
    original_list = approval_service.list_pending
    original_resolve = approval_service.resolve
    approval_service.create_pending = AsyncMock(
        return_value=SimpleNamespace(
            id=approval_id,
            project_id=None,
            task_id=None,
            status="pending",
            reason="need approval",
            approver_identifier=None,
        )
    )
    approval_service.list_pending = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=approval_id,
                project_id=None,
                task_id=None,
                status="pending",
                reason="need approval",
                approver_identifier=None,
            )
        ]
    )
    approval_service.resolve = AsyncMock(
        return_value=SimpleNamespace(
            id=approval_id,
            project_id=None,
            task_id=None,
            status="approved",
            reason="need approval",
            approver_identifier="ops@example.com",
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/approvals",
            json={"reason": "need approval"},
        )
        list_response = await client.get("/api/v1/approvals?status=pending")
        resolve_response = await client.post(
            f"/api/v1/approvals/{approval_id}/resolve",
            json={"status": "approved", "approver_identifier": "ops@example.com"},
        )

    approval_service.create_pending = original_create
    approval_service.list_pending = original_list
    approval_service.resolve = original_resolve

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert resolve_response.json()["status"] == "approved"


async def test_policy_and_security_routes() -> None:
    app = build_test_app()
    rule_id = uuid.uuid4()
    key_id = uuid.uuid4()
    now = datetime.now(UTC)
    api_key = SimpleNamespace(
        id=key_id,
        key_id="abcd1234",
        name="Ops",
        token_preview="abc123",
        issued_at=now,
        expires_at=now + timedelta(days=30),
        revoked_at=None,
        last_used_at=None,
    )
    original_create_rule = policy_rule_service.create_rule
    original_list_rules = policy_rule_service.list_rules
    original_create_key = api_key_service.create_key
    original_list_keys = api_key_service.list_keys
    policy_rule_service.create_rule = AsyncMock(
        return_value=SimpleNamespace(
            id=rule_id,
            project_id=None,
            rule_type="privacy",
            name="local-only",
            enabled=True,
            config={"enforce": True},
        )
    )
    policy_rule_service.list_rules = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=rule_id,
                project_id=None,
                rule_type="privacy",
                name="local-only",
                enabled=True,
                config={"enforce": True},
            )
        ]
    )
    api_key_service.create_key = AsyncMock(return_value=("secret-token", api_key))
    api_key_service.list_keys = AsyncMock(return_value=[api_key])

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_rule = await client.post(
            "/api/v1/policies/rules",
            json={"rule_type": "privacy", "name": "local-only", "config": {"enforce": True}},
        )
        list_rules = await client.get("/api/v1/policies/rules")
        create_key = await client.post(
            "/api/v1/security/api-keys",
            json={"name": "Ops", "ttl_days": 30},
        )
        list_keys = await client.get("/api/v1/security/api-keys")

    policy_rule_service.create_rule = original_create_rule
    policy_rule_service.list_rules = original_list_rules
    api_key_service.create_key = original_create_key
    api_key_service.list_keys = original_list_keys

    assert create_rule.status_code == 201
    assert list_rules.status_code == 200
    assert create_key.status_code == 201
    assert create_key.json()["raw_token"] == "secret-token"
    assert list_keys.status_code == 200


async def test_semantic_cache_route() -> None:
    app = build_test_app()
    import api.v1.cache as cache_module

    original_list_entries = cache_module.semantic_cache_service.list_entries
    cache_module.semantic_cache_service.list_entries = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=uuid.uuid4(),
                project_id=None,
                normalized_prompt="hello",
                model_family="gpt-4o-mini",
                system_prompt_hash="hash",
                response_payload={"response": "cached-value", "local_only": True},
                embedding=[0.1, 0.2],
                generated_locally=True,
            )
        ]
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/cache/semantic")

    cache_module.semantic_cache_service.list_entries = original_list_entries

    assert response.status_code == 200
    assert response.json()[0]["local_only"] is True
    assert response.json()[0]["normalized_prompt"] == "hello"
