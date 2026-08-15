from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentRole(str, enum.Enum):
    COORDINATOR = "coordinator"
    REASONING = "reasoning"
    RESEARCH = "research"
    CODING = "coding"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    CRITIC = "critic"
    SUMMARIZER = "summarizer"


class AgentState(str, enum.Enum):
    IDLE = "idle"
    SPAWNING = "spawning"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"  # blocked on another agent
    DONE = "done"
    FAILED = "failed"
    KILLED = "killed"


class AgentSpec(BaseModel):
    role: AgentRole
    preferred_provider: str | None = None
    preferred_model: str | None = None
    system_prompt: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    allow_tools: bool = True
    local_only: bool = False
    description: str = ""


class AgentProcess(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    state: AgentState = AgentState.IDLE
    mission_id: str | None = None
    spec: AgentSpec
    assigned_provider: str | None = None
    assigned_model: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_summary: str | None = None
    error: str | None = None
    token_usage: dict = Field(default_factory=dict)


class IPCMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str
    topic: str
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


ROLE_SPECS: dict[AgentRole, AgentSpec] = {
    AgentRole.COORDINATOR: AgentSpec(
        role=AgentRole.COORDINATOR,
        preferred_provider="anthropic",
        preferred_model="claude-sonnet-4-6",
        system_prompt="You are the coordinator. Decompose the mission into sub-tasks and delegate to specialist agents. Synthesize their outputs into a final answer.",
        max_tokens=8192,
        temperature=0.3,
        description="Orchestrates other agents. Owns the mission plan.",
    ),
    AgentRole.REASONING: AgentSpec(
        role=AgentRole.REASONING,
        preferred_provider="anthropic",
        preferred_model="claude-opus-4-7",
        system_prompt="You are a deep reasoning agent. Think step by step, explore edge cases, and provide rigorous analysis.",
        max_tokens=16384,
        temperature=0.1,
        description="Deep chain-of-thought reasoning for complex problems.",
    ),
    AgentRole.RESEARCH: AgentSpec(
        role=AgentRole.RESEARCH,
        preferred_provider="gemini",
        preferred_model="gemini-2.5-pro",
        system_prompt="You are a research agent. Gather facts, cite sources, and produce structured summaries.",
        max_tokens=8192,
        temperature=0.5,
        description="Long-context research and fact gathering.",
    ),
    AgentRole.CODING: AgentSpec(
        role=AgentRole.CODING,
        preferred_provider="openai",
        preferred_model="gpt-4o",
        system_prompt="You are a coding agent. Write clean, correct, production-ready code with minimal explanation.",
        max_tokens=8192,
        temperature=0.2,
        allow_tools=True,
        description="Code generation, review, and debugging.",
    ),
    AgentRole.SYNTHESIS: AgentSpec(
        role=AgentRole.SYNTHESIS,
        preferred_provider="anthropic",
        preferred_model="claude-haiku-4-5",
        system_prompt="You are a synthesis agent. Merge multiple agent outputs into a coherent, non-redundant response.",
        max_tokens=4096,
        temperature=0.4,
        description="Merges outputs from multiple agents.",
    ),
    AgentRole.VALIDATION: AgentSpec(
        role=AgentRole.VALIDATION,
        preferred_provider="groq",
        preferred_model="llama-3.3-70b-versatile",
        system_prompt="You are a validation agent. Check outputs for correctness, completeness, and consistency. Flag issues.",
        max_tokens=2048,
        temperature=0.0,
        description="Fast validation and correctness checking.",
    ),
    AgentRole.CRITIC: AgentSpec(
        role=AgentRole.CRITIC,
        preferred_provider="grok",
        preferred_model="grok-3",
        system_prompt="You are a critic agent. Identify weaknesses, assumptions, and blind spots in the proposed solution.",
        max_tokens=4096,
        temperature=0.6,
        description="Adversarial critique of agent outputs.",
    ),
    AgentRole.SUMMARIZER: AgentSpec(
        role=AgentRole.SUMMARIZER,
        preferred_provider="groq",
        preferred_model="llama-3.1-8b-instant",
        system_prompt="You are a summarizer. Produce concise, factual summaries. No padding.",
        max_tokens=1024,
        temperature=0.3,
        description="Fast, cheap summarization.",
    ),
}
