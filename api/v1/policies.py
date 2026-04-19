from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.policy_rule_service import policy_rule_service
from services.policy_service import PolicyEvaluation, policy_service

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyRuleCreateRequest(BaseModel):
    project_id: uuid.UUID | None = None
    rule_type: str
    name: str
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class PolicyRuleUpdateRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class PolicyRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    rule_type: str
    name: str
    enabled: bool
    config: dict


class PolicyEvaluationRequest(BaseModel):
    text: str
    provider_name: str
    local_only: bool = False
    token_quota: int | None = None
    estimated_tokens: int = 0
    task_type: str = "chat"


class PolicyEvaluationResponse(PolicyEvaluation):
    pass


@router.post("/rules", response_model=PolicyRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_policy_rule(
    payload: PolicyRuleCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PolicyRuleResponse:
    rule = await policy_rule_service.create_rule(db, **payload.model_dump())
    return PolicyRuleResponse.model_validate(rule)


@router.get("/rules", response_model=list[PolicyRuleResponse])
async def list_policy_rules(
    project_id: uuid.UUID | None = None,
    rule_type: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[PolicyRuleResponse]:
    rules = await policy_rule_service.list_rules(
        db,
        project_id=project_id,
        rule_type=rule_type,
    )
    return [PolicyRuleResponse.model_validate(rule) for rule in rules]


@router.patch("/rules/{rule_id}", response_model=PolicyRuleResponse)
async def update_policy_rule(
    rule_id: uuid.UUID,
    payload: PolicyRuleUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PolicyRuleResponse:
    rule = await policy_rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Policy rule not found.")
    updated = await policy_rule_service.update_rule(
        db,
        rule=rule,
        updates=payload.model_dump(exclude_unset=True),
    )
    return PolicyRuleResponse.model_validate(updated)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    rule = await policy_rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Policy rule not found.")
    await policy_rule_service.delete_rule(db, rule=rule)


@router.post("/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_policy(
    payload: PolicyEvaluationRequest,
) -> PolicyEvaluationResponse:
    evaluation = policy_service.evaluate_routing(**payload.model_dump())
    return PolicyEvaluationResponse(**evaluation.model_dump())
