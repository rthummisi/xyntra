from __future__ import annotations

import threading
from collections import defaultdict

from agents.types import AgentProcess, AgentRole, AgentState, ROLE_SPECS, AgentSpec


class AgentRegistry:
    """In-memory registry of all live AgentProcess instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agents: dict[str, AgentProcess] = {}
        self._by_mission: dict[str, list[str]] = defaultdict(list)

    def register(self, agent: AgentProcess) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent
            if agent.mission_id:
                self._by_mission[agent.mission_id].append(agent.agent_id)

    def get(self, agent_id: str) -> AgentProcess | None:
        return self._agents.get(agent_id)

    def list_all(self) -> list[AgentProcess]:
        return list(self._agents.values())

    def list_by_mission(self, mission_id: str) -> list[AgentProcess]:
        ids = self._by_mission.get(mission_id, [])
        return [self._agents[i] for i in ids if i in self._agents]

    def list_by_state(self, state: AgentState) -> list[AgentProcess]:
        return [a for a in self._agents.values() if a.state == state]

    def update_state(self, agent_id: str, state: AgentState) -> None:
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].state = state

    def remove(self, agent_id: str) -> None:
        with self._lock:
            agent = self._agents.pop(agent_id, None)
            if agent and agent.mission_id:
                ids = self._by_mission.get(agent.mission_id, [])
                self._by_mission[agent.mission_id] = [i for i in ids if i != agent_id]

    def spec_for_role(self, role: AgentRole) -> AgentSpec:
        return ROLE_SPECS[role].model_copy()

    def active_count(self) -> int:
        return sum(
            1 for a in self._agents.values()
            if a.state in (AgentState.RUNNING, AgentState.SPAWNING, AgentState.WAITING)
        )


agent_registry = AgentRegistry()
