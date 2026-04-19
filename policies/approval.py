from __future__ import annotations

from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    required: bool
    reason: str | None = None


class ApprovalPolicy:
    def requires_approval(
        self,
        *,
        task_type: str,
        local_only: bool,
    ) -> ApprovalDecision:
        if task_type in {"deployment", "destructive"}:
            return ApprovalDecision(required=True, reason="high_risk_task")
        if not local_only and task_type == "external_call":
            return ApprovalDecision(required=True, reason="hosted_provider_use")
        return ApprovalDecision(required=False)


approval_policy = ApprovalPolicy()
