from __future__ import annotations

from unittest.mock import Mock

import workers.dlq_worker as dlq_worker


def test_retry_dead_letter_delegates_to_async_handler() -> None:
    original_run = dlq_worker.asyncio.run

    def fake_run(coroutine):
        coroutine.close()
        return {
            "status": "requeued",
            "dead_letter_id": "entry-1",
            "retry_count": 1,
            "payload": {"task_id": "task-1"},
        }

    dlq_worker.asyncio.run = Mock(side_effect=fake_run)

    try:
        result = dlq_worker.retry_dead_letter("00000000-0000-0000-0000-000000000001")
    finally:
        dlq_worker.asyncio.run = original_run

    assert result["status"] == "requeued"
    assert result["retry_count"] == 1
