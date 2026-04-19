from __future__ import annotations

from pydantic import BaseModel


class CostDecision(BaseModel):
    allowed: bool
    reason: str | None = None


class CostPolicy:
    def enforce_quota(
        self,
        *,
        token_quota: int | None,
        estimated_tokens: int,
    ) -> CostDecision:
        if token_quota is not None and estimated_tokens > token_quota:
            return CostDecision(allowed=False, reason="QuotaExceeded")
        return CostDecision(allowed=True)


cost_policy = CostPolicy()
