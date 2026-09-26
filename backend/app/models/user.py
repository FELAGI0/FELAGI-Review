from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String)
    github_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer)
    review_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
