from __future__ import annotations

from dataclasses import dataclass

from hardware.inventory import SystemInventory
from hardware.model_hw_matrix import get_requirements, models_fitting_vram
from kernel.task_classifier import ComputeTarget, KernelClassification, TaskComplexity, TaskSensitivity
from providers.capability_registry import ModelCapability, capability_registry


@dataclass
class ModelSelection:
    provider: str
    model: str
    quantization: str  # "full" | "8bit" | "4bit" | "api"
    rationale: str
    fallback_chain: list[tuple[str, str]]


def select_model(
    classification: KernelClassification,
    hw: SystemInventory | None,
    force_local: bool = False,
) -> ModelSelection:
    """Pick provider+model+quantization based on task classification and hardware."""

    free_vram = hw.free_vram_gb if hw else 0.0
    has_gpu = hw.has_cuda or hw.has_mps if hw else False

    # Secret/confidential must run locally
    must_local = (
        force_local
        or classification.sensitivity in (TaskSensitivity.CONFIDENTIAL, TaskSensitivity.SECRET)
        or classification.compute_target == ComputeTarget.LOCAL_CPU
    )

    # Try local GPU path
    if has_gpu and free_vram > 0 and (must_local or classification.compute_target in (ComputeTarget.LOCAL_GPU, ComputeTarget.HYBRID)):
        for quant in ("full", "8bit", "4bit"):
            candidates = models_fitting_vram(free_vram, prefer_quantization=quant)
            if candidates:
                best = candidates[0]
                fallbacks = [(c.provider, c.model) for c in candidates[1:4]]
                return ModelSelection(
                    provider=best.provider,
                    model=best.model,
                    quantization=quant,
                    rationale=f"Local GPU | {free_vram:.1f}GB free VRAM | {quant} quant | task={classification.complexity.value}",
                    fallback_chain=fallbacks,
                )

    # CPU fallback for must-local
    if must_local:
        return ModelSelection(
            provider="ollama",
            model="llama3.2:3b",
            quantization="4bit",
            rationale="CPU fallback | sensitivity requires local | no GPU available",
            fallback_chain=[("ollama", "llama3.2:1b")],
        )

    # Cloud API selection: Inkling owns reasoning/analysis, Nemotron owns code.
    # Both are ranked highest in the capability registry so routing naturally
    # surfaces them first; the explicit map below locks that preference in the
    # kernel path as well.
    is_coding = (
        classification.task_type == "tool_use"
        or "coding" in classification.agent_roles_suggested
    )

    if classification.complexity == TaskComplexity.EXTREME:
        if is_coding:
            provider, model = "nemotron", "llama-3.1-nemotron-70b-instruct"
            fallbacks = [("inkling", "inkling-1"), ("anthropic", "claude-opus-4-7"), ("openai", "gpt-4o")]
        else:
            provider, model = "inkling", "inkling-1"
            # deepseek-reasoner is R1-class chain-of-thought — strong second for reasoning
            fallbacks = [("deepseek", "deepseek-reasoner"), ("anthropic", "claude-opus-4-7"), ("gemini", "gemini-2.5-pro")]
    elif classification.complexity == TaskComplexity.COMPLEX:
        if is_coding:
            provider, model = "nemotron", "llama-3.1-nemotron-70b-instruct"
            fallbacks = [("inkling", "inkling-1-mini"), ("anthropic", "claude-sonnet-4-6"), ("openai", "gpt-4o")]
        else:
            provider, model = "inkling", "inkling-1"
            fallbacks = [("deepseek", "deepseek-reasoner"), ("anthropic", "claude-sonnet-4-6"), ("openai", "gpt-4o")]
    elif classification.complexity == TaskComplexity.MODERATE:
        if is_coding:
            provider, model = "nemotron", "llama-3.1-nemotron-8b-instruct"
            fallbacks = [("openai", "gpt-4o-mini"), ("groq", "llama-3.3-70b-versatile")]
        else:
            provider, model = "inkling", "inkling-1-mini"
            fallbacks = [("openai", "gpt-4o-mini"), ("anthropic", "claude-haiku-4-5")]
    else:  # TRIVIAL
        provider, model = "groq", "llama-3.1-8b-instant"
        fallbacks = [("openai", "gpt-3.5-turbo")]

    return ModelSelection(
        provider=provider,
        model=model,
        quantization="api",
        rationale=(
            f"Cloud API | complexity={classification.complexity.value}"
            f" | {'code' if is_coding else 'reasoning'} path"
            f" | sensitivity={classification.sensitivity.value}"
        ),
        fallback_chain=fallbacks,
    )
