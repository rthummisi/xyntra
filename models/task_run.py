import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaskRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "task_runs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    worker_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    task = relationship("Task", back_populates="runs", lazy="selectin")
    provider_calls = relationship(
        "ProviderCall",
        back_populates="task_run",
        lazy="selectin",
    )
