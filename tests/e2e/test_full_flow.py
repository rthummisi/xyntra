from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.provider_call import ProviderCall
from models.task import Task
from models.task_run import TaskRun
from tasks.executor import task_executor


async def test_full_flow_project_to_replay(
    e2e_client,
    e2e_session: AsyncSession,
    seeded_owner,
) -> None:
    project_response = await e2e_client.post(
        "/api/v1/projects",
        json={
            "owner_id": str(seeded_owner.id),
            "name": "E2E Project",
            "description": "Flow test",
            "local_only": False,
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    task_response = await e2e_client.post(
        "/api/v1/tasks",
        json={
            "project_id": project_id,
            "name": "Summarize",
            "task_type": "chat",
            "input_payload": {"prompt": "hello"},
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    queue_response = await e2e_client.post(f"/api/v1/tasks/{task_id}/queue")
    assert queue_response.status_code == 200
    task_run_id = queue_response.json()["id"]

    task = await e2e_session.get(Task, task_id)
    task_run = await e2e_session.get(TaskRun, task_run_id)
    await task_executor.start_run(e2e_session, task, task_run)
    await task_executor.complete_run(
        e2e_session,
        task=task,
        task_run=task_run,
        output_payload={"content": "done"},
    )
    e2e_session.add(
        ProviderCall(
            project_id=task.project_id,
            session_id=task.session_id,
            task_run_id=task_run.id,
            provider_name="ollama",
            model_name="llama3.2:3b",
            request_payload={"prompt": "hello"},
            response_payload={"content": "done"},
            input_tokens=4,
            output_tokens=1,
            cost_usd=0.0,
            cache_hit=False,
        )
    )
    await e2e_session.commit()

    replay_response = await e2e_client.get(f"/api/v1/replay/{task_run_id}")

    assert replay_response.status_code == 200
    payload = replay_response.json()["payload"]
    assert payload["task_run"]["status"] == "completed"
    assert payload["provider_calls"][0]["provider_name"] == "ollama"
