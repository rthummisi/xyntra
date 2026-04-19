from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from services.approval_service import approval_service


async def test_create_pending_approval() -> None:
    session = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock(
        side_effect=lambda approval: setattr(approval, "id", uuid.uuid4())
    )

    approval = await approval_service.create_pending(
        session,
        project_id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        reason="hosted provider use",
    )

    assert approval.status == "pending"
    assert approval.reason == "hosted provider use"


async def test_resolve_approval_updates_status() -> None:
    session = AsyncMock()
    approval_id = uuid.uuid4()
    approval = SimpleNamespace(
        id=approval_id,
        status="pending",
        approver_identifier=None,
    )
    session.get.return_value = approval

    resolved = await approval_service.resolve(
        session,
        approval_id=approval_id,
        status="approved",
        approver_identifier="admin@example.com",
    )

    assert resolved is approval
    assert resolved.status == "approved"
    assert resolved.approver_identifier == "admin@example.com"
