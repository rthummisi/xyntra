from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from agents.ipc import ipc_bus
from agents.registry import agent_registry
from agents.types import AgentProcess, AgentRole, AgentState, ROLE_SPECS, IPCMessage
from providers.base.adapter import UnifiedMessage, UnifiedRequest
from providers.registry import provider_registry


class MissionResult:
    def __init__(self, mission_id: str) -> None:
        self.mission_id = mission_id
        self.agent_outputs: dict[str, str] = {}
        self.errors: dict[str, str] = {}
        self.started_at = datetime.utcnow()
        self.finished_at: datetime | None = None

    def add_output(self, agent_id: str, content: str) -> None:
        self.agent_outputs[agent_id] = content

    def add_error(self, agent_id: str, error: str) -> None:
        self.errors[agent_id] = error

    def complete(self) -> None:
        self.finished_at = datetime.utcnow()

    @property
    def elapsed_ms(self) -> float:
        end = self.finished_at or datetime.utcnow()
        return (end - self.started_at).total_seconds() * 1000


async def _run_agent(
    agent: AgentProcess,
    user_message: str,
    result: MissionResult,
) -> None:
    agent_registry.update_state(agent.agent_id, AgentState.RUNNING)
    agent.started_at = datetime.utcnow()

    spec = agent.spec
    provider_name = agent.assigned_provider or spec.preferred_provider or "anthropic"
    model = agent.assigned_model or spec.preferred_model or "claude-haiku-4-5"

    try:
        adapter = provider_registry.get(provider_name)
        req = UnifiedRequest(
            model=model,
            messages=[
                UnifiedMessage(role="user", content=user_message),
            ],
            system_prompt=spec.system_prompt,
            metadata={"agent_id": agent.agent_id, "role": agent.role.value},
        )
        response = await adapter.complete(req)
        result.add_output(agent.agent_id, response.content)
        agent.result_summary = response.content[:500]
        agent.token_usage = response.usage
        agent_registry.update_state(agent.agent_id, AgentState.DONE)
    except Exception as exc:
        result.add_error(agent.agent_id, str(exc))
        agent.error = str(exc)
        agent_registry.update_state(agent.agent_id, AgentState.FAILED)

    agent.finished_at = datetime.utcnow()

    # Notify coordinator via IPC
    coordinator_agents = [
        a for a in agent_registry.list_by_mission(agent.mission_id or "")
        if a.role == AgentRole.COORDINATOR and a.agent_id != agent.agent_id
    ]
    for coord in coordinator_agents:
        ipc_bus.send(IPCMessage(
            from_agent=agent.agent_id,
            to_agent=coord.agent_id,
            topic="agent_done",
            payload={"agent_id": agent.agent_id, "role": agent.role.value, "ok": agent.error is None},
        ))


class AgentDispatcher:
    """Spawns and coordinates a fleet of agents for a mission."""

    async def dispatch(
        self,
        roles: list[AgentRole],
        user_message: str,
        mission_id: str | None = None,
        provider_overrides: dict[AgentRole, tuple[str, str]] | None = None,
    ) -> MissionResult:
        mission_id = mission_id or str(uuid.uuid4())
        result = MissionResult(mission_id)

        agents: list[AgentProcess] = []
        for role in roles:
            spec = ROLE_SPECS[role].model_copy()
            provider_override = (provider_overrides or {}).get(role)
            agent = AgentProcess(
                name=f"{role.value}-{mission_id[:8]}",
                role=role,
                state=AgentState.SPAWNING,
                mission_id=mission_id,
                spec=spec,
                assigned_provider=provider_override[0] if provider_override else spec.preferred_provider,
                assigned_model=provider_override[1] if provider_override else spec.preferred_model,
            )
            agent_registry.register(agent)
            agents.append(agent)

        # Run all agents concurrently (coordinator waits for the rest if present)
        coordinator = next((a for a in agents if a.role == AgentRole.COORDINATOR), None)
        workers = [a for a in agents if a.role != AgentRole.COORDINATOR]

        worker_tasks = [asyncio.create_task(_run_agent(a, user_message, result)) for a in workers]
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        if coordinator:
            # Feed coordinator the worker results
            worker_summary = "\n\n".join(
                f"[{agent_registry.get(aid).role.value if agent_registry.get(aid) else 'agent'}]\n{out}"
                for aid, out in result.agent_outputs.items()
            )
            coord_prompt = f"Mission objective:\n{user_message}\n\nAgent outputs:\n{worker_summary}\n\nSynthesize a final answer."
            await _run_agent(coordinator, coord_prompt, result)

        result.complete()
        return result


dispatcher = AgentDispatcher()
