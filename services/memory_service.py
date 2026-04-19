from __future__ import annotations

import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from memory.preference_memory import preference_memory_store
from memory.project_memory import project_memory_store
from memory.session_memory import session_memory_store
from memory.summary_memory import summary_memory_store


class MemorySnapshot(BaseModel):
    session_messages: list[dict]
    session_summaries: list[dict]
    project_state: dict | None
    project_decisions: list[dict]
    user_preferences: list[dict]


class MemoryService:
    async def snapshot(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MemorySnapshot:
        messages = await session_memory_store.fetch_messages(
            session,
            session_id=session_id,
        )
        summaries = await summary_memory_store.list_summaries(
            session,
            session_id=session_id,
        )
        project_state = await project_memory_store.fetch_project_state(
            session,
            project_id=project_id,
        )
        project_decisions = await project_memory_store.list_decisions(
            session,
            project_id=project_id,
        )
        preferences = await preference_memory_store.list_user_preferences(
            session,
            user_id=user_id,
        )

        return MemorySnapshot(
            session_messages=[
                {
                    "id": str(message.id),
                    "role": message.role,
                    "content": message.content,
                    "sequence_number": message.sequence_number,
                }
                for message in messages
            ],
            session_summaries=[
                {
                    "id": str(summary.id),
                    "summary_type": summary.summary_type,
                    "content": summary.content,
                    "token_count": summary.token_count,
                }
                for summary in summaries
            ],
            project_state=project_state.state if project_state is not None else None,
            project_decisions=[
                {
                    "id": str(decision.id),
                    "decision_type": decision.decision_type,
                    "summary": decision.summary,
                }
                for decision in project_decisions
            ],
            user_preferences=[
                {
                    "id": str(template.id),
                    "name": template.name,
                    "version": template.version,
                    "tags": template.tags,
                }
                for template in preferences
            ],
        )


memory_service = MemoryService()
