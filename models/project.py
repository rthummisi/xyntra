import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_quota: Mapped[int | None] = mapped_column(nullable=True)

    owner = relationship("User", back_populates="projects", lazy="selectin")
    state = relationship("ProjectState", back_populates="project", uselist=False)
    sessions = relationship("Session", back_populates="project", lazy="selectin")
    tasks = relationship("Task", back_populates="project", lazy="selectin")
    artifacts = relationship("Artifact", back_populates="project", lazy="selectin")
    decisions = relationship("Decision", back_populates="project", lazy="selectin")
