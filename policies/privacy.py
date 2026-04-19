from __future__ import annotations

from pydantic import BaseModel


class PrivacyDecision(BaseModel):
    allowed: bool
    reason: str | None = None


class PrivacyPolicy:
    def enforce_local_only(
        self,
        *,
        local_only: bool,
        provider_name: str,
    ) -> PrivacyDecision:
        if local_only and provider_name != "ollama":
            return PrivacyDecision(allowed=False, reason="PrivacyViolation")
        return PrivacyDecision(allowed=True)


privacy_policy = PrivacyPolicy()
