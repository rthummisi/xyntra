from __future__ import annotations

from pydantic import BaseModel, Field


class ContentGuardResult(BaseModel):
    blocked: bool
    reasons: list[str] = Field(default_factory=list)


class ContentGuard:
    banned_terms = ["malware payload", "credential stuffing"]

    def inspect(self, text: str) -> ContentGuardResult:
        reasons = [term for term in self.banned_terms if term in text.lower()]
        return ContentGuardResult(blocked=bool(reasons), reasons=reasons)


content_guard = ContentGuard()
