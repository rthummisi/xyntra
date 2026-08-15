from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelHWRequirement:
    provider: str
    model: str
    vram_full_gb: float      # FP16 / BF16 full precision
    vram_8bit_gb: float      # INT8 quantized
    vram_4bit_gb: float      # INT4/GGUF Q4 quantized
    min_ram_gb: float        # system RAM minimum (for offloading)
    preferred_gpu_count: int = 1
    supports_cpu_only: bool = True


# VRAM estimates — conservative figures. Actual depends on context length.
_MATRIX: list[ModelHWRequirement] = [
    # Ollama local models
    ModelHWRequirement("ollama", "llama3.2:1b",    vram_full_gb=2,   vram_8bit_gb=1,   vram_4bit_gb=0.8,  min_ram_gb=4),
    ModelHWRequirement("ollama", "llama3.2:3b",    vram_full_gb=4,   vram_8bit_gb=2,   vram_4bit_gb=1.5,  min_ram_gb=8),
    ModelHWRequirement("ollama", "llama3.2:11b",   vram_full_gb=16,  vram_8bit_gb=10,  vram_4bit_gb=7,    min_ram_gb=16),
    ModelHWRequirement("ollama", "llama3.2:90b",   vram_full_gb=90,  vram_8bit_gb=50,  vram_4bit_gb=30,   min_ram_gb=64, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "llama3.3:70b",   vram_full_gb=70,  vram_8bit_gb=40,  vram_4bit_gb=22,   min_ram_gb=64, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "llama3.1:8b",    vram_full_gb=10,  vram_8bit_gb=6,   vram_4bit_gb=4,    min_ram_gb=12),
    ModelHWRequirement("ollama", "llama3.1:70b",   vram_full_gb=70,  vram_8bit_gb=40,  vram_4bit_gb=22,   min_ram_gb=64, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "llama3.1:405b",  vram_full_gb=400, vram_8bit_gb=220, vram_4bit_gb=110,  min_ram_gb=256, preferred_gpu_count=8, supports_cpu_only=False),
    ModelHWRequirement("ollama", "qwen2.5:7b",     vram_full_gb=8,   vram_8bit_gb=5,   vram_4bit_gb=3.5,  min_ram_gb=12),
    ModelHWRequirement("ollama", "qwen2.5:14b",    vram_full_gb=16,  vram_8bit_gb=9,   vram_4bit_gb=6,    min_ram_gb=20),
    ModelHWRequirement("ollama", "qwen2.5:32b",    vram_full_gb=32,  vram_8bit_gb=18,  vram_4bit_gb=12,   min_ram_gb=40, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "qwen2.5:72b",    vram_full_gb=72,  vram_8bit_gb=40,  vram_4bit_gb=24,   min_ram_gb=64, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "qwen2.5-coder:7b",  vram_full_gb=8,  vram_8bit_gb=5,  vram_4bit_gb=3.5, min_ram_gb=12),
    ModelHWRequirement("ollama", "qwen2.5-coder:32b", vram_full_gb=32, vram_8bit_gb=18, vram_4bit_gb=12,  min_ram_gb=40, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "phi4:14b",       vram_full_gb=16,  vram_8bit_gb=9,   vram_4bit_gb=6,    min_ram_gb=20),
    ModelHWRequirement("ollama", "gemma3:27b",     vram_full_gb=28,  vram_8bit_gb=16,  vram_4bit_gb=10,   min_ram_gb=32),
    ModelHWRequirement("ollama", "deepseek-r1:7b", vram_full_gb=8,   vram_8bit_gb=5,   vram_4bit_gb=3.5,  min_ram_gb=12),
    ModelHWRequirement("ollama", "deepseek-r1:14b",vram_full_gb=16,  vram_8bit_gb=9,   vram_4bit_gb=6,    min_ram_gb=20),
    ModelHWRequirement("ollama", "deepseek-r1:32b",vram_full_gb=32,  vram_8bit_gb=18,  vram_4bit_gb=12,   min_ram_gb=40, preferred_gpu_count=2),
    ModelHWRequirement("ollama", "deepseek-r1:70b",vram_full_gb=70,  vram_8bit_gb=40,  vram_4bit_gb=22,   min_ram_gb=64, preferred_gpu_count=2),
    # Nemotron (NVIDIA NIM, self-hosted)
    ModelHWRequirement("nemotron", "nemotron-4-340b-instruct", vram_full_gb=340, vram_8bit_gb=180, vram_4bit_gb=90,  min_ram_gb=256, preferred_gpu_count=8, supports_cpu_only=False),
    ModelHWRequirement("nemotron", "llama-3.1-nemotron-70b-instruct", vram_full_gb=70, vram_8bit_gb=40, vram_4bit_gb=22, min_ram_gb=64, preferred_gpu_count=2),
    ModelHWRequirement("nemotron", "llama-3.1-nemotron-8b-instruct",  vram_full_gb=10, vram_8bit_gb=6,  vram_4bit_gb=4,  min_ram_gb=12),
    # API-only (no local VRAM requirement)
    ModelHWRequirement("anthropic", "claude-opus-4-7",           vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("anthropic", "claude-sonnet-4-6",         vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("openai",    "gpt-4o",                    vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("gemini",    "gemini-2.5-pro",            vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("grok",      "grok-3",                    vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("groq",      "llama-3.3-70b-versatile",   vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("inkling",   "inkling-1",                    vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("inkling",   "inkling-1-mini",               vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("nemotron",  "nemotron-4-340b-instruct-api", vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("qwen",      "qwen-max",                     vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("qwen",      "qwen-plus",                    vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("qwen",      "qwen-turbo",                   vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
    ModelHWRequirement("qwen",      "qwen2.5-72b-instruct",         vram_full_gb=0, vram_8bit_gb=0, vram_4bit_gb=0, min_ram_gb=0, supports_cpu_only=True),
]

_INDEX: dict[str, ModelHWRequirement] = {
    f"{r.provider}:{r.model}": r for r in _MATRIX
}


def get_requirements(provider: str, model: str) -> ModelHWRequirement | None:
    return _INDEX.get(f"{provider}:{model}")


def models_fitting_vram(available_vram_gb: float, prefer_quantization: str = "full") -> list[ModelHWRequirement]:
    """Return local models that fit in the given VRAM, sorted by quality (larger = better)."""
    results = []
    for req in _MATRIX:
        if req.vram_full_gb == 0:
            continue  # skip API-only
        if prefer_quantization == "full" and req.vram_full_gb <= available_vram_gb:
            results.append(req)
        elif prefer_quantization == "8bit" and req.vram_8bit_gb <= available_vram_gb:
            results.append(req)
        elif prefer_quantization == "4bit" and req.vram_4bit_gb <= available_vram_gb:
            results.append(req)
    results.sort(key=lambda r: r.vram_full_gb, reverse=True)
    return results
