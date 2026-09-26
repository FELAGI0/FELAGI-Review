from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, OrgRole, Plan


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    plan: Mapped[Plan] = mapped_column(Enum(Plan), default=Plan.free)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    members: Mapped[list["Membership"]] = relationship(back_populates="organization")


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[OrgRole] = mapped_column(Enum(OrgRole), default=OrgRole.member)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    organization: Mapped[Organization] = relationship(back_populates="members")
