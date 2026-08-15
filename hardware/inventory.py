from __future__ import annotations

import subprocess
import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GPUDevice:
    index: int
    name: str
    vram_total_mb: int
    vram_used_mb: int
    vram_free_mb: int
    utilization_pct: float
    temperature_c: float
    power_draw_w: float
    driver_version: str = ""

    @property
    def vram_total_gb(self) -> float:
        return round(self.vram_total_mb / 1024, 1)

    @property
    def vram_free_gb(self) -> float:
        return round(self.vram_free_mb / 1024, 1)

    @property
    def vram_pressure(self) -> str:
        ratio = self.vram_used_mb / max(self.vram_total_mb, 1)
        if ratio < 0.5:
            return "low"
        if ratio < 0.8:
            return "medium"
        return "high"


@dataclass
class SystemInventory:
    gpus: list[GPUDevice] = field(default_factory=list)
    cpu_cores: int = 0
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    has_cuda: bool = False
    has_mps: bool = False  # Apple Silicon
    sampled_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_vram_gb(self) -> float:
        return sum(g.vram_total_gb for g in self.gpus)

    @property
    def free_vram_gb(self) -> float:
        return sum(g.vram_free_gb for g in self.gpus)

    @property
    def best_gpu(self) -> GPUDevice | None:
        if not self.gpus:
            return None
        return max(self.gpus, key=lambda g: g.vram_free_mb)


def _probe_nvidia() -> list[GPUDevice]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,driver_version",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []

    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9:
            continue
        try:
            gpus.append(
                GPUDevice(
                    index=int(parts[0]),
                    name=parts[1],
                    vram_total_mb=int(parts[2]),
                    vram_used_mb=int(parts[3]),
                    vram_free_mb=int(parts[4]),
                    utilization_pct=float(re.sub(r"[^\d.]", "", parts[5]) or 0),
                    temperature_c=float(re.sub(r"[^\d.]", "", parts[6]) or 0),
                    power_draw_w=float(re.sub(r"[^\d.]", "", parts[7]) or 0),
                    driver_version=parts[8],
                )
            )
        except (ValueError, IndexError):
            continue
    return gpus


def _probe_mps() -> bool:
    """Detect Apple Silicon MPS (Metal Performance Shaders)."""
    try:
        out = subprocess.check_output(["sysctl", "-n", "hw.optional.arm64"], text=True, timeout=2)
        return out.strip() == "1"
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def _probe_ram() -> tuple[float, float]:
    try:
        import psutil
        mem = psutil.virtual_memory()
        return round(mem.total / 1024**3, 1), round(mem.available / 1024**3, 1)
    except ImportError:
        return 0.0, 0.0


def _probe_cpu() -> int:
    try:
        import os
        return os.cpu_count() or 0
    except Exception:
        return 0


def snapshot() -> SystemInventory:
    gpus = _probe_nvidia()
    has_mps = _probe_mps() if not gpus else False
    ram_total, ram_avail = _probe_ram()
    return SystemInventory(
        gpus=gpus,
        cpu_cores=_probe_cpu(),
        ram_total_gb=ram_total,
        ram_available_gb=ram_avail,
        has_cuda=len(gpus) > 0,
        has_mps=has_mps,
        sampled_at=datetime.utcnow(),
    )
