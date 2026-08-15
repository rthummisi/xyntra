from __future__ import annotations

from fastapi import APIRouter

from hardware.health_monitor import hw_monitor
from hardware.inventory import snapshot
from hardware.model_hw_matrix import models_fitting_vram

router = APIRouter(tags=["hardware"])


@router.get("/hardware/snapshot")
async def hw_snapshot() -> dict:
    inv = snapshot()
    return {
        "gpus": [
            {
                "index": g.index,
                "name": g.name,
                "vram_total_gb": g.vram_total_gb,
                "vram_free_gb": g.vram_free_gb,
                "vram_used_mb": g.vram_used_mb,
                "utilization_pct": g.utilization_pct,
                "temperature_c": g.temperature_c,
                "power_draw_w": g.power_draw_w,
                "vram_pressure": g.vram_pressure,
            }
            for g in inv.gpus
        ],
        "cpu_cores": inv.cpu_cores,
        "ram_total_gb": inv.ram_total_gb,
        "ram_available_gb": inv.ram_available_gb,
        "has_cuda": inv.has_cuda,
        "has_mps": inv.has_mps,
        "total_vram_gb": inv.total_vram_gb,
        "free_vram_gb": inv.free_vram_gb,
        "sampled_at": inv.sampled_at.isoformat(),
    }


@router.get("/hardware/live")
async def hw_live() -> dict:
    inv = hw_monitor.current or snapshot()
    gpus = [
        {
            "index": g.index,
            "name": g.name,
            "vram_total_gb": g.vram_total_gb,
            "vram_free_gb": g.vram_free_gb,
            "utilization_pct": g.utilization_pct,
            "temperature_c": g.temperature_c,
            "vram_pressure": g.vram_pressure,
        }
        for g in inv.gpus
    ]
    return {
        "gpus": gpus,
        "has_cuda": inv.has_cuda,
        "has_mps": inv.has_mps,
        "free_vram_gb": inv.free_vram_gb,
        "ram_available_gb": inv.ram_available_gb,
        "sampled_at": inv.sampled_at.isoformat(),
    }


@router.get("/hardware/models/fitting")
async def models_fitting(vram_gb: float = 0.0, quantization: str = "full") -> list[dict]:
    if vram_gb <= 0:
        inv = hw_monitor.current or snapshot()
        vram_gb = inv.free_vram_gb
    results = models_fitting_vram(vram_gb, prefer_quantization=quantization)
    return [
        {
            "provider": r.provider,
            "model": r.model,
            "vram_full_gb": r.vram_full_gb,
            "vram_8bit_gb": r.vram_8bit_gb,
            "vram_4bit_gb": r.vram_4bit_gb,
            "min_ram_gb": r.min_ram_gb,
        }
        for r in results
    ]
