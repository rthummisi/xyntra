from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.ipc import ipc_bus
from agents.registry import agent_registry
from agents.types import AgentRole, AgentState
from orchestrator.dispatcher import dispatcher

router = APIRouter(tags=["agents"])


class MissionRequest(BaseModel):
    objective: str
    roles: list[str] | None = None  # defaults to coordinator + reasoning + synthesis
    mission_id: str | None = None


class MissionResponse(BaseModel):
    mission_id: str
    agent_count: int
    outputs: dict[str, str]
    errors: dict[str, str]
    elapsed_ms: float


@router.post("/agents/missions", response_model=MissionResponse)
async def run_mission(req: MissionRequest) -> MissionResponse:
    role_names = req.roles or ["coordinator", "reasoning", "synthesis", "validation"]
    try:
        roles = [AgentRole(r) for r in role_names]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    result = await dispatcher.dispatch(
        roles=roles,
        user_message=req.objective,
        mission_id=req.mission_id,
    )
    return MissionResponse(
        mission_id=result.mission_id,
        agent_count=len(result.agent_outputs) + len(result.errors),
        outputs=result.agent_outputs,
        errors=result.errors,
        elapsed_ms=result.elapsed_ms,
    )


@router.get("/agents")
async def list_agents() -> list[dict]:
    return [a.model_dump() for a in agent_registry.list_all()]


@router.get("/agents/active")
async def active_agents() -> dict:
    running = agent_registry.list_by_state(AgentState.RUNNING)
    spawning = agent_registry.list_by_state(AgentState.SPAWNING)
    return {
        "active_count": agent_registry.active_count(),
        "running": [a.model_dump() for a in running],
        "spawning": [a.model_dump() for a in spawning],
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.model_dump()


@router.delete("/agents/{agent_id}")
async def kill_agent(agent_id: str) -> dict:
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_registry.update_state(agent_id, AgentState.KILLED)
    ipc_bus.clear_agent(agent_id)
    return {"agent_id": agent_id, "state": "killed"}


@router.get("/agents/ipc/history")
async def ipc_history(limit: int = 50) -> list[dict]:
    return [m.model_dump() for m in ipc_bus.history(limit=limit)]


@router.get("/agents/roles/catalog")
async def roles_catalog() -> list[dict]:
    from agents.types import ROLE_SPECS
    return [
        {
            "role": role.value,
            "description": spec.description,
            "preferred_provider": spec.preferred_provider,
            "preferred_model": spec.preferred_model,
            "max_tokens": spec.max_tokens,
        }
        for role, spec in ROLE_SPECS.items()
    ]
