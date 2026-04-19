from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.webhook import WebhookEvent, WebhookSubscription
from workers.webhook_worker import deliver_webhook_event


class EventBus:
    async def emit(
        self,
        session: AsyncSession,
        *,
        event_type: str,
        payload: dict,
        subscription_id: uuid.UUID | None = None,
    ) -> WebhookEvent:
        if subscription_id is not None:
            subscription = await session.get(WebhookSubscription, subscription_id)
            if subscription is None:
                raise ValueError("Webhook subscription not found.")
            return await self._create_and_dispatch_event(
                session,
                subscription=subscription,
                event_type=event_type,
                payload=payload,
            )

        subscriptions = await self._matching_subscriptions(
            session,
            event_type=event_type,
            project_id=payload.get("project_id"),
        )
        if not subscriptions:
            return await self._create_event(
                session,
                subscription=None,
                event_type=event_type,
                payload=payload,
            )

        first_event: WebhookEvent | None = None
        for subscription in subscriptions:
            event = await self._create_and_dispatch_event(
                session,
                subscription=subscription,
                event_type=event_type,
                payload=payload,
            )
            if first_event is None:
                first_event = event
        return first_event

    async def list_events(
        self,
        session: AsyncSession,
        *,
        event_type: str | None = None,
        project_id: str | None = None,
        provider_name: str | None = None,
    ) -> list[WebhookEvent]:
        query = select(WebhookEvent).order_by(WebhookEvent.created_at.desc())
        if event_type is not None:
            query = query.where(WebhookEvent.event_type == event_type)
        result = await session.execute(query)
        events = list(result.scalars().all())
        if project_id is not None:
            events = [
                event
                for event in events
                if str(event.payload.get("project_id")) == project_id
            ]
        if provider_name is not None:
            events = [
                event
                for event in events
                if event.payload.get("provider_name") == provider_name
            ]
        return events

    async def _matching_subscriptions(
        self,
        session: AsyncSession,
        *,
        event_type: str,
        project_id: str | None,
    ) -> list[WebhookSubscription]:
        result = await session.execute(
            select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
        )
        subscriptions = list(result.scalars().all())
        return [
            subscription
            for subscription in subscriptions
            if event_type in subscription.event_types
            and (
                subscription.project_id is None
                or project_id is None
                or str(subscription.project_id) == project_id
            )
        ]

    async def _create_and_dispatch_event(
        self,
        session: AsyncSession,
        *,
        subscription: WebhookSubscription,
        event_type: str,
        payload: dict,
    ) -> WebhookEvent:
        event = await self._create_event(
            session,
            subscription=subscription,
            event_type=event_type,
            payload=payload,
        )
        deliver_webhook_event.delay(
            event_id=str(event.id),
            target_url=subscription.target_url,
            secret=subscription.secret,
            payload=payload,
        )
        return event

    async def _create_event(
        self,
        session: AsyncSession,
        *,
        subscription: WebhookSubscription | None,
        event_type: str,
        payload: dict,
    ) -> WebhookEvent:
        event = WebhookEvent(
            subscription_id=None if subscription is None else subscription.id,
            event_type=event_type,
            payload=payload,
            delivery_status="pending",
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


event_bus = EventBus()
