from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from memory.session_memory import session_memory_store
from memory.summary_memory import summary_memory_store


class ContextCompactor:
    async def compact_if_needed(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
        token_threshold: int,
    ) -> bool:
        messages = await session_memory_store.fetch_messages(
            session,
            session_id=session_id,
        )
        token_estimate = sum(len(message.content.split()) for message in messages)
        if token_estimate <= token_threshold:
            return False

        summary_content = "\n".join(
            f"{message.role}: {message.content}" for message in messages[-10:]
        )
        await summary_memory_store.create_summary(
            session,
            session_id=session_id,
            content=summary_content,
            token_count=token_estimate,
            summary_type="compacted",
        )
        return True


context_compactor = ContextCompactor()
