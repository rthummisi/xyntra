from __future__ import annotations

import asyncio
import hashlib
import hmac
import json

import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import get_settings
from models.webhook import WebhookEvent
from workers.celery_app import celery_app

settings = get_settings()


def build_signature(secret: str, payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@celery_app.task(
    name="xyntra.webhooks.deliver",
    bind=True,
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def deliver_webhook_event(
    self,
    *,
    event_id: str,
    target_url: str,
    secret: str,
    payload: dict,
) -> dict:
    signature = build_signature(secret, payload)
    try:
        response = httpx.post(
            target_url,
            json=payload,
            headers={"X-Xyntra-Signature": signature, "X-Xyntra-Event-ID": event_id},
            timeout=10.0,
        )
        response.raise_for_status()
        asyncio.run(
            _update_event_delivery(
                event_id=event_id,
                delivery_status="delivered",
                error_message=None,
                attempt_count=self.request.retries + 1,
            )
        )
        return {"status": "delivered", "event_id": event_id}
    except httpx.HTTPError as exc:
        delivery_status = "failed" if self.request.retries >= 4 else "retrying"
        asyncio.run(
            _update_event_delivery(
                event_id=event_id,
                delivery_status=delivery_status,
                error_message=str(exc),
                attempt_count=self.request.retries + 1,
            )
        )
        raise


async def _update_event_delivery(
    *,
    event_id: str,
    delivery_status: str,
    error_message: str | None,
    attempt_count: int,
) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                update(WebhookEvent)
                .where(WebhookEvent.id == event_id)
                .values(
                    delivery_status=delivery_status,
                    error_message=error_message,
                    attempt_count=attempt_count,
                )
            )
    finally:
        await engine.dispose()
