from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.provider_call import ProviderCall
from services.replay_service import replay_service
from services.task_service import task_service
from tasks.executor import task_executor


async def test_task_lifecycle_and_replay(
    integration_session: AsyncSession,
    seeded_project,
    seeded_session,
) -> None:
    task = await task_service.create_task(
        integration_session,
        project_id=seeded_project.id,
        session_id=seeded_session.id,
        name="Summarize repo",
        task_type="chat",
        input_payload={"prompt": "summarize"},
        description="Integration lifecycle",
    )

    task_run = await task_service.queue_task(integration_session, task)
    await task_executor.start_run(integration_session, task, task_run)
    completed_run = await task_executor.complete_run(
        integration_session,
        task=task,
        task_run=task_run,
        output_payload={"content": "summary"},
    )

    integration_session.add(
        ProviderCall(
            project_id=seeded_project.id,
            session_id=seeded_session.id,
            task_run_id=completed_run.id,
            provider_name="ollama",
            model_name="llama3.2:3b",
            request_payload={"prompt": "summarize"},
            response_payload={"content": "summary"},
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.0,
            cache_hit=False,
        )
    )
    await integration_session.commit()

    replay = await replay_service.replay_task_run(
        integration_session,
        task_run_id=completed_run.id,
    )

    assert replay["task"]["name"] == "Summarize repo"
    assert replay["task_run"]["status"] == "completed"
    assert replay["task_run"]["attempt_number"] == 1
    assert replay["task_run"]["output_payload"] == {"content": "summary"}
    assert replay["provider_calls"][0]["provider_name"] == "ollama"
    assert replay["provider_calls"][0]["request_payload"] == {"prompt": "summarize"}


async def test_dlq_entry_round_trip(
    integration_session: AsyncSession,
) -> None:
    entry = await task_service.push_to_dlq(
        integration_session,
        task_name="failed-task",
        payload={"step": 1},
        error_message="boom",
    )

    dlq_entries = await task_service.list_dlq(integration_session)

    assert dlq_entries
    assert dlq_entries[0].id == entry.id
    assert dlq_entries[0].last_error == "boom"
