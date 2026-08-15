from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from hardware.health_monitor import hw_monitor
from hardware.inventory import snapshot
from kernel.model_selector import select_model
from kernel.task_classifier import kernel_classifier
from providers.base.adapter import UnifiedMessage, UnifiedRequest

router = APIRouter(tags=["kernel"])


class KernelDecisionRequest(BaseModel):
    messages: list[dict]
    local_only: bool = False
    metadata: dict = {}


@router.post("/kernel/decide")
async def kernel_decide(req: KernelDecisionRequest) -> dict:
    unified = UnifiedRequest(
        model="",
        messages=[UnifiedMessage(**m) for m in req.messages],
        metadata={**req.metadata, "local_only": req.local_only},
    )
    classification = kernel_classifier.classify(unified)
    hw = hw_monitor.current or snapshot()
    selection = select_model(classification, hw, force_local=req.local_only)

    return {
        "classification": classification.model_dump(),
        "selection": {
            "provider": selection.provider,
            "model": selection.model,
            "quantization": selection.quantization,
            "rationale": selection.rationale,
            "fallback_chain": selection.fallback_chain,
        },
        "hardware": {
            "free_vram_gb": hw.free_vram_gb,
            "has_cuda": hw.has_cuda,
            "has_mps": hw.has_mps,
            "gpu_count": len(hw.gpus),
        },
    }
