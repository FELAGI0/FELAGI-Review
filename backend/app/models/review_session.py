from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, ReviewSessionStatus


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    pr_id: Mapped[UUID] = mapped_column(ForeignKey("pull_requests.id"))
    status: Mapped[ReviewSessionStatus] = mapped_column(
        Enum(ReviewSessionStatus), default=ReviewSessionStatus.pending
    )
    model_used: Mapped[str | None] = mapped_column(String)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    summary: Mapped[str | None] = mapped_column(Text)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    comments: Mapped[list["AIComment"]] = relationship(  # noqa: F821
        back_populates="session"
    )
