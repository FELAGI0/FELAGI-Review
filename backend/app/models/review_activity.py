from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ReviewAction


class ReviewActivity(Base):
    __tablename__ = "review_activity"
    __table_args__ = (Index("ix_review_activity_user_created", "user_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    pr_id: Mapped[UUID] = mapped_column(ForeignKey("pull_requests.id"))
    action: Mapped[ReviewAction] = mapped_column(Enum(ReviewAction))
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
