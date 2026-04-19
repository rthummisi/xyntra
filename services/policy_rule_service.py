from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import PolicyRule


class PolicyRuleService:
    async def create_rule(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None,
        rule_type: str,
        name: str,
        enabled: bool = True,
        config: dict | None = None,
    ) -> PolicyRule:
        rule = PolicyRule(
            project_id=project_id,
            rule_type=rule_type,
            name=name,
            enabled=enabled,
            config=config or {},
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def list_rules(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID | None = None,
        rule_type: str | None = None,
    ) -> list[PolicyRule]:
        query = select(PolicyRule).order_by(PolicyRule.created_at.desc())
        if project_id is not None:
            query = query.where(PolicyRule.project_id == project_id)
        if rule_type is not None:
            query = query.where(PolicyRule.rule_type == rule_type)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_rule(
        self,
        session: AsyncSession,
        rule_id: uuid.UUID,
    ) -> PolicyRule | None:
        return await session.get(PolicyRule, rule_id)

    async def update_rule(
        self,
        session: AsyncSession,
        *,
        rule: PolicyRule,
        updates: dict,
    ) -> PolicyRule:
        for field, value in updates.items():
            setattr(rule, field, value)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def delete_rule(self, session: AsyncSession, *, rule: PolicyRule) -> None:
        await session.delete(rule)
        await session.commit()


policy_rule_service = PolicyRuleService()
