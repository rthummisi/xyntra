from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.webhook import WebhookSubscription

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookSubscriptionCreateRequest(BaseModel):
    project_id: uuid.UUID | None = None
    target_url: str
    secret: str
    event_types: list[str] = Field(default_factory=list)
    is_active: bool = True


class WebhookSubscriptionUpdateRequest(BaseModel):
    target_url: str | None = None
    secret: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None


class WebhookSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    target_url: str
    secret: str
    event_types: list[str]
    is_active: bool


@router.post(
    "",
    response_model=WebhookSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_subscription(
    payload: WebhookSubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> WebhookSubscriptionResponse:
    subscription = WebhookSubscription(**payload.model_dump())
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return WebhookSubscriptionResponse.model_validate(subscription)


@router.get("", response_model=list[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[WebhookSubscriptionResponse]:
    query = select(WebhookSubscription).order_by(WebhookSubscription.created_at.desc())
    if project_id is not None:
        query = query.where(WebhookSubscription.project_id == project_id)
    result = await db.execute(query)
    subscriptions = list(result.scalars().all())
    return [
        WebhookSubscriptionResponse.model_validate(subscription)
        for subscription in subscriptions
    ]


@router.get("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> WebhookSubscriptionResponse:
    subscription = await db.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    return WebhookSubscriptionResponse.model_validate(subscription)


@router.patch("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: uuid.UUID,
    payload: WebhookSubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> WebhookSubscriptionResponse:
    subscription = await db.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)
    await db.commit()
    await db.refresh(subscription)
    return WebhookSubscriptionResponse.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    subscription = await db.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    await db.delete(subscription)
    await db.commit()
