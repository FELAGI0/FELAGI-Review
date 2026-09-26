from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_pr_file_line", "pr_id", "file_path", "line_number"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    pr_id: Mapped[UUID] = mapped_column(ForeignKey("pull_requests.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("comments.id"))
    file_path: Mapped[str | None] = mapped_column(String)
    line_number: Mapped[int | None] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
