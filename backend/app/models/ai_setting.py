from sqlalchemy import ARRAY, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Severity


class AISetting(Base):
    __tablename__ = "ai_settings"
    __table_args__ = (UniqueConstraint("repo_id"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    repo_id: Mapped[UUID] = mapped_column(ForeignKey("repositories.id"))
    enabled_checks: Mapped[dict] = mapped_column(JSONB)
    custom_rules: Mapped[str | None] = mapped_column(Text)
    ignore_paths: Mapped[list[str]] = mapped_column(ARRAY(String))
    severity_threshold: Mapped[Severity] = mapped_column(
        Enum(Severity), default=Severity.warning
    )
