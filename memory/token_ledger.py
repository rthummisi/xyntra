from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

_LEDGER_PATH = Path("artifacts/token_ledger.json")

# Providers/models where wasting tokens is expensive
_PREMIUM_PROVIDERS = {"inkling", "nemotron"}
_PREMIUM_MODEL_FRAGMENTS = {"opus", "deepseek-reasoner", "nemotron-4-340b"}

# Token thresholds for grading
_TINY_TOKENS = 300     # under this = trivial exchange
_HEAVY_TOKENS = 1_500  # over this = genuinely complex


def _grade(
    provider: str,
    model: str,
    total_tokens: int,
    task_type: str,
) -> tuple[str, str]:
    """Return (efficiency, reason). efficiency is 'productive' | 'useless'."""
    is_premium = provider in _PREMIUM_PROVIDERS or any(
        f in model for f in _PREMIUM_MODEL_FRAGMENTS
    )
    is_trivial = total_tokens < _TINY_TOKENS and task_type == "chat"
    is_heavy = total_tokens >= _HEAVY_TOKENS or task_type in ("tool_use", "multimodal")

    if is_premium and is_trivial:
        return (
            "useless",
            f"Only {total_tokens} tokens on a premium model — a groq/economy model would have been sufficient",
        )
    if not is_premium and is_heavy:
        return (
            "productive",
            f"Economy model handled {total_tokens}-token task efficiently",
        )
    return "productive", "Model tier matched task scope"


@dataclass
class TokenEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_summary: str = ""
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    task_type: str = "chat"
    cache_hit: bool = False
    efficiency: str = "productive"
    efficiency_reason: str = ""


class TokenLedger:
    def __init__(self) -> None:
        self._entries: list[TokenEntry] = []
        self._load()

    def record(
        self,
        *,
        task_summary: str,
        provider: str,
        model: str,
        usage: dict,
        task_type: str = "chat",
        cache_hit: bool = False,
    ) -> TokenEntry:
        prompt_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
        completion_tokens = int(
            usage.get("completion_tokens", usage.get("output_tokens", 0))
        )
        total_tokens = int(
            usage.get("total_tokens", prompt_tokens + completion_tokens)
        )

        if cache_hit:
            efficiency, reason = "productive", "Served from cache — no API tokens consumed"
        else:
            efficiency, reason = _grade(provider, model, total_tokens, task_type)

        entry = TokenEntry(
            task_summary=task_summary[:120],
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            task_type=task_type,
            cache_hit=cache_hit,
            efficiency=efficiency,
            efficiency_reason=reason,
        )
        self._entries.append(entry)
        self._persist()
        return entry

    def all(self, limit: int = 200) -> list[TokenEntry]:
        return list(reversed(self._entries))[:limit]

    def totals(self) -> dict:
        entries = self._entries
        return {
            "total_entries": len(entries),
            "total_tokens": sum(e.total_tokens for e in entries),
            "prompt_tokens": sum(e.prompt_tokens for e in entries),
            "completion_tokens": sum(e.completion_tokens for e in entries),
            "productive": sum(1 for e in entries if e.efficiency == "productive"),
            "useless": sum(1 for e in entries if e.efficiency == "useless"),
        }

    def _persist(self) -> None:
        try:
            _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            _LEDGER_PATH.write_text(
                json.dumps([asdict(e) for e in self._entries], indent=2)
            )
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if _LEDGER_PATH.exists():
                raw = json.loads(_LEDGER_PATH.read_text())
                self._entries = [TokenEntry(**item) for item in raw]
        except Exception:
            self._entries = []


token_ledger = TokenLedger()
