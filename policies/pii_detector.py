from __future__ import annotations

import re

from pydantic import BaseModel, Field


class PIIResult(BaseModel):
    detected: bool
    redacted_text: str
    findings: list[str] = Field(default_factory=list)


class PIIDetector:
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    phone_pattern = re.compile(
        r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
    )

    def redact(self, text: str) -> PIIResult:
        findings: list[str] = []
        redacted = text
        if self.email_pattern.search(redacted):
            redacted = self.email_pattern.sub("[REDACTED_EMAIL]", redacted)
            findings.append("email")
        if self.phone_pattern.search(redacted):
            redacted = self.phone_pattern.sub("[REDACTED_PHONE]", redacted)
            findings.append("phone")
        return PIIResult(
            detected=bool(findings),
            redacted_text=redacted,
            findings=findings,
        )


pii_detector = PIIDetector()
