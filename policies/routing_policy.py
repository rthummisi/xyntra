from __future__ import annotations

from pydantic import BaseModel, Field

from policies.approval import approval_policy
from policies.content_guard import content_guard
from policies.cost import cost_policy
from policies.injection_guard import injection_guard
from policies.pii_detector import pii_detector


class RoutingPolicyResult(BaseModel):
    allowed: bool
    redacted_text: str
    reasons: list[str] = Field(default_factory=list)
    approval_required: bool = False


class RoutingPolicy:
    def evaluate(
        self,
        *,
        text: str,
        token_quota: int | None,
        estimated_tokens: int,
        task_type: str = "chat",
        local_only: bool = False,
    ) -> RoutingPolicyResult:
        pii = pii_detector.redact(text)
        injection = injection_guard.inspect(pii.redacted_text)
        content = content_guard.inspect(pii.redacted_text)
        cost = cost_policy.enforce_quota(
            token_quota=token_quota,
            estimated_tokens=estimated_tokens,
        )
        approval = approval_policy.requires_approval(
            task_type=task_type,
            local_only=local_only,
        )
        reasons = list(pii.findings) + injection.reasons + content.reasons
        if not cost.allowed and cost.reason:
            reasons.append(cost.reason)
        allowed = not injection.blocked and not content.blocked and cost.allowed
        return RoutingPolicyResult(
            allowed=allowed,
            redacted_text=pii.redacted_text,
            reasons=reasons,
            approval_required=approval.required,
        )


routing_policy = RoutingPolicy()
