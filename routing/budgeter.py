from __future__ import annotations

from pydantic import BaseModel


class BudgetDecision(BaseModel):
    allowed: bool
    reason: str | None = None


class BudgetEnforcer:
    def evaluate(
        self,
        *,
        token_quota: int | None,
        estimated_tokens: int,
    ) -> BudgetDecision:
        if token_quota is None:
            return BudgetDecision(allowed=True)
        if estimated_tokens > token_quota:
            return BudgetDecision(allowed=False, reason="QuotaExceeded")
        return BudgetDecision(allowed=True)


budget_enforcer = BudgetEnforcer()
