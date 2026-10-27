from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Provider


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    provider: Mapped[Provider] = mapped_column(Enum(Provider), default=Provider.github)
    external_id: Mapped[int] = mapped_column(BigInteger)
    github_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    installation_id: Mapped[int | None] = mapped_column(BigInteger)
    full_name: Mapped[str] = mapped_column(String)
    webhook_secret: Mapped[str | None] = mapped_column(String)
    access_token_encrypted: Mapped[str | None] = mapped_column(String)
    auto_review_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
