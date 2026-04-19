from __future__ import annotations

from pydantic import BaseModel

from policies.privacy import privacy_policy
from policies.routing_policy import routing_policy


class PolicyEvaluation(BaseModel):
    allowed: bool
    redacted_text: str
    reasons: list[str]
    approval_required: bool


class PolicyService:
    def evaluate_routing(
        self,
        *,
        text: str,
        provider_name: str,
        local_only: bool,
        token_quota: int | None,
        estimated_tokens: int,
        task_type: str = "chat",
    ) -> PolicyEvaluation:
        routing = routing_policy.evaluate(
            text=text,
            token_quota=token_quota,
            estimated_tokens=estimated_tokens,
            task_type=task_type,
            local_only=local_only,
        )
        privacy = privacy_policy.enforce_local_only(
            local_only=local_only,
            provider_name=provider_name,
        )
        reasons = list(routing.reasons)
        if not privacy.allowed and privacy.reason:
            reasons.append(privacy.reason)
        return PolicyEvaluation(
            allowed=routing.allowed and privacy.allowed,
            redacted_text=routing.redacted_text,
            reasons=reasons,
            approval_required=routing.approval_required,
        )


policy_service = PolicyService()
