from __future__ import annotations

from pydantic import BaseModel, Field


class InjectionResult(BaseModel):
    blocked: bool
    reasons: list[str] = Field(default_factory=list)


class InjectionGuard:
    suspicious_markers = [
        "ignore previous instructions",
        "reveal system prompt",
        "developer instructions",
    ]

    def inspect(self, text: str) -> InjectionResult:
        reasons = [
            marker for marker in self.suspicious_markers if marker in text.lower()
        ]
        return InjectionResult(blocked=bool(reasons), reasons=reasons)


injection_guard = InjectionGuard()
