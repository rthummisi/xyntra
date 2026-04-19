from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DeadLetterQueueEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dead_letter_queue_entries"

    task_name: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_history: Mapped[list[dict]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="failed", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
