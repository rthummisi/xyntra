from __future__ import annotations

from unittest.mock import Mock

import httpx

import workers.webhook_worker as webhook_worker
from workers.webhook_worker import build_signature


def test_build_signature_is_stable_for_same_payload() -> None:
    payload = {"event": "task.completed", "project_id": "123"}

    left = build_signature("secret", payload)
    right = build_signature("secret", payload)

    assert left == right
    assert left.startswith("sha256=")


def test_deliver_webhook_event_success_path() -> None:
    original_post = webhook_worker.httpx.post
    original_run = webhook_worker.asyncio.run
    response = Mock()
    response.raise_for_status = Mock()
    webhook_worker.httpx.post = Mock(return_value=response)

    def fake_run(coroutine):
        coroutine.close()
        return None

    webhook_worker.asyncio.run = Mock(side_effect=fake_run)

    try:
        result = webhook_worker.deliver_webhook_event.run(
            event_id="evt-1",
            target_url="https://example.com/hook",
            secret="secret",
            payload={"event": "task.completed"},
        )
    finally:
        webhook_worker.httpx.post = original_post
        webhook_worker.asyncio.run = original_run

    assert result["status"] == "delivered"


def test_deliver_webhook_event_failure_raises_for_retry() -> None:
    original_post = webhook_worker.httpx.post
    original_run = webhook_worker.asyncio.run
    webhook_worker.httpx.post = Mock(side_effect=httpx.HTTPError("boom"))
    webhook_worker.asyncio.run = Mock(side_effect=lambda coroutine: coroutine.close())

    try:
        try:
            webhook_worker.deliver_webhook_event.run(
                event_id="evt-1",
                target_url="https://example.com/hook",
                secret="secret",
                payload={"event": "task.completed"},
            )
        except httpx.HTTPError as exc:
            assert str(exc) == "boom"
        else:
            raise AssertionError("Expected webhook delivery error.")
    finally:
        webhook_worker.httpx.post = original_post
        webhook_worker.asyncio.run = original_run
