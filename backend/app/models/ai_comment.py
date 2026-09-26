from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AICategory, Base, Severity
from .review_session import ReviewSession


class AIComment(Base):
    __tablename__ = "ai_comments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("review_sessions.id"))
    file_path: Mapped[str] = mapped_column(String)
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    category: Mapped[AICategory] = mapped_column(Enum(AICategory))
    message: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text)
    code_snippet: Mapped[str | None] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    session: Mapped[ReviewSession] = relationship(back_populates="comments")
