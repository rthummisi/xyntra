import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SemanticCacheEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semantic_cache_entries"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    normalized_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_family: Mapped[str] = mapped_column(String(120), nullable=False)
    system_prompt_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    generated_locally: Mapped[bool] = mapped_column(default=False, nullable=False)
