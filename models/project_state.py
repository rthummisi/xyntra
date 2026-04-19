import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_states"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    project = relationship("Project", back_populates="state", lazy="selectin")
