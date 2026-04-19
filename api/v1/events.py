from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.events import event_bus

router = APIRouter(prefix="/events", tags=["events"])


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID | None
    event_type: str
    payload: dict
    delivery_status: str
    attempt_count: int
    error_message: str | None


@router.get("", response_model=list[EventResponse])
async def list_events(
    event_type: str | None = None,
    project_id: str | None = None,
    provider_name: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[EventResponse]:
    events = await event_bus.list_events(
        db,
        event_type=event_type,
        project_id=project_id,
        provider_name=provider_name,
    )
    return [EventResponse.model_validate(event) for event in events]
