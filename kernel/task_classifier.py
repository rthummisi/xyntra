from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel

from providers.base.adapter import UnifiedRequest


class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"       # single-agent, fast model
    MODERATE = "moderate"     # single-agent, capable model
    COMPLEX = "complex"       # multi-agent recommended
    EXTREME = "extreme"       # multi-agent + reasoning agent required


class TaskSensitivity(str, Enum):
    PUBLIC = "public"         # can use any provider
    INTERNAL = "internal"     # prefer local or trusted cloud
    CONFIDENTIAL = "confidential"  # local only
    SECRET = "secret"         # local only, no logging


class ComputeTarget(str, Enum):
    API = "api"               # call a cloud provider
    LOCAL_GPU = "local_gpu"   # run on local GPU via Ollama/vLLM
    LOCAL_CPU = "local_cpu"   # CPU-only fallback
    HYBRID = "hybrid"         # split across local + API


class KernelClassification(BaseModel):
    # original routing fields
    task_type: str
    requires_multimodal: bool
    requires_tools: bool
    preferred_strategy: str
    # new kernel fields
    complexity: TaskComplexity
    sensitivity: TaskSensitivity
    compute_target: ComputeTarget
    estimated_tokens: int
    multi_agent_recommended: bool
    agent_roles_suggested: list[str]
    reasoning: str


_CONFIDENTIAL_PATTERNS = re.compile(
    r"\b(password|secret|private.?key|api.?key|token|credential|ssn|social.?security|credit.?card|dob|date.of.birth)\b",
    re.IGNORECASE,
)
_CODE_PATTERNS = re.compile(
    r"\b(def |class |function |import |require|#include|SELECT|INSERT|UPDATE|DELETE|CREATE TABLE)\b"
)
_RESEARCH_PATTERNS = re.compile(
    r"\b(research|survey|literature|papers|studies|evidence|sources|citations|summarize.{0,20}article)\b",
    re.IGNORECASE,
)
_REASONING_PATTERNS = re.compile(
    r"\b(why|how|explain|analyze|critique|evaluate|compare|reason|think through|step.by.step|proof|derive)\b",
    re.IGNORECASE,
)


def _content_text(request: UnifiedRequest) -> str:
    return " ".join(
        m.content if isinstance(m.content, str) else str(m.content)
        for m in request.messages
    )


def _estimate_tokens(text: str) -> int:
    return max(100, len(text.split()) * 4 // 3)


class KernelClassifier:
    def classify(self, request: UnifiedRequest) -> KernelClassification:
        text = _content_text(request)
        lower = text.lower()
        estimated = _estimate_tokens(text)

        # --- sensitivity ---
        if _CONFIDENTIAL_PATTERNS.search(text):
            sensitivity = TaskSensitivity.CONFIDENTIAL
        elif "internal" in lower or "confidential" in lower:
            sensitivity = TaskSensitivity.INTERNAL
        else:
            sensitivity = TaskSensitivity.PUBLIC

        # --- task type ---
        has_images = any(
            isinstance(m.content, list) for m in request.messages
        ) or bool(request.attachments)
        has_tools = bool(request.tool_definitions)

        if has_images:
            task_type = "multimodal"
        elif has_tools or _CODE_PATTERNS.search(text):
            task_type = "tool_use"
        else:
            task_type = "chat"

        # --- complexity ---
        word_count = len(text.split())
        reasoning_hit = bool(_REASONING_PATTERNS.search(text))
        research_hit = bool(_RESEARCH_PATTERNS.search(text))
        code_hit = bool(_CODE_PATTERNS.search(text))
        multi_hit = reasoning_hit and (research_hit or code_hit)

        if word_count > 500 or multi_hit:
            complexity = TaskComplexity.EXTREME
        elif word_count > 150 or reasoning_hit or research_hit:
            complexity = TaskComplexity.COMPLEX
        elif word_count > 40:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.TRIVIAL

        # --- compute target ---
        local_only = request.metadata.get("local_only", False)
        if sensitivity in (TaskSensitivity.CONFIDENTIAL, TaskSensitivity.SECRET) or local_only:
            compute_target = ComputeTarget.LOCAL_GPU
        elif complexity in (TaskComplexity.EXTREME, TaskComplexity.COMPLEX) and not local_only:
            compute_target = ComputeTarget.HYBRID
        else:
            compute_target = ComputeTarget.API

        # --- multi-agent ---
        multi_agent = complexity in (TaskComplexity.COMPLEX, TaskComplexity.EXTREME)

        agent_roles: list[str] = []
        if multi_agent:
            agent_roles.append("coordinator")
            if reasoning_hit:
                agent_roles.append("reasoning")
            if research_hit:
                agent_roles.append("research")
            if code_hit:
                agent_roles.append("coding")
            agent_roles.append("synthesis")
            agent_roles.append("validation")

        # --- strategy ---
        if multi_agent:
            strategy = "multi_agent_parallel"
        elif task_type == "multimodal":
            strategy = "multimodal_direct"
        elif task_type == "tool_use":
            strategy = "tool_use_chain"
        else:
            strategy = "direct"

        reasoning_parts = [
            f"complexity={complexity.value}",
            f"sensitivity={sensitivity.value}",
            f"~{estimated} tokens",
        ]
        if multi_agent:
            reasoning_parts.append(f"roles={','.join(agent_roles)}")

        return KernelClassification(
            task_type=task_type,
            requires_multimodal=has_images,
            requires_tools=has_tools,
            preferred_strategy=strategy,
            complexity=complexity,
            sensitivity=sensitivity,
            compute_target=compute_target,
            estimated_tokens=estimated,
            multi_agent_recommended=multi_agent,
            agent_roles_suggested=agent_roles,
            reasoning=" | ".join(reasoning_parts),
        )


kernel_classifier = KernelClassifier()
