from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.events import event_bus
from models.message import Message
from models.session import Session


class SessionService:
    async def create_session(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        status: str = "active",
    ) -> Session:
        db_session = Session(
            project_id=project_id,
            user_id=user_id,
            title=title,
            status=status,
        )
        session.add(db_session)
        await session.commit()
        await session.refresh(db_session)
        return db_session

    async def list_sessions(
        self,
        session: AsyncSession,
        *,
        project_id: uuid.UUID,
    ) -> list[Session]:
        result = await session.execute(
            select(Session)
            .where(Session.project_id == project_id)
            .order_by(Session.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_session(
        self,
        session: AsyncSession,
        session_id: uuid.UUID,
    ) -> Session | None:
        return await session.get(Session, session_id)

    async def list_messages(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
    ) -> list[Message]:
        result = await session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence_number.asc())
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        session: AsyncSession,
        *,
        session_id: uuid.UUID,
        role: str,
        content: str,
        attachments: list[dict] | None = None,
        parent_message_id: uuid.UUID | None = None,
    ) -> Message:
        result = await session.execute(
            select(func.coalesce(func.max(Message.sequence_number), 0)).where(
                Message.session_id == session_id
            )
        )
        next_sequence = int(result.scalar_one()) + 1

        message = Message(
            session_id=session_id,
            parent_message_id=parent_message_id,
            role=role,
            content=content,
            sequence_number=next_sequence,
            attachments=attachments or [],
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    async def branch_session(
        self,
        session: AsyncSession,
        *,
        source_session: Session,
        branch_from_message_id: uuid.UUID,
        title: str,
    ) -> Session:
        branch = Session(
            project_id=source_session.project_id,
            user_id=source_session.user_id,
            parent_session_id=source_session.id,
            title=title,
            status="active",
        )
        session.add(branch)
        await session.flush()

        messages_result = await session.execute(
            select(Message)
            .where(Message.session_id == source_session.id)
            .where(
                Message.sequence_number
                <= self._branch_cutoff_subquery(branch_from_message_id)
            )
            .order_by(Message.sequence_number.asc())
        )
        source_messages = list(messages_result.scalars().all())

        for source_message in source_messages:
            session.add(
                Message(
                    session_id=branch.id,
                    role=source_message.role,
                    content=source_message.content,
                    sequence_number=source_message.sequence_number,
                    attachments=source_message.attachments,
                )
            )

        await session.commit()
        await session.refresh(branch)
        await event_bus.emit(
            session,
            event_type="session.branched",
            payload={
                "project_id": str(branch.project_id),
                "source_session_id": str(source_session.id),
                "branch_session_id": str(branch.id),
                "branch_from_message_id": str(branch_from_message_id),
                "title": branch.title,
            },
        )
        return branch

    @staticmethod
    def _branch_cutoff_subquery(message_id: uuid.UUID):
        return (
            select(Message.sequence_number)
            .where(Message.id == message_id)
            .scalar_subquery()
        )


session_service = SessionService()
