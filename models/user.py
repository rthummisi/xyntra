from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects = relationship("Project", back_populates="owner", lazy="selectin")
    sessions = relationship("Session", back_populates="user", lazy="selectin")
    prompt_templates = relationship(
        "PromptTemplate",
        back_populates="user",
        lazy="selectin",
    )
