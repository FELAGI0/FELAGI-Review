from enum import StrEnum

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    pass


class UserRole(StrEnum):
    admin = "admin"
    reviewer = "reviewer"
    viewer = "viewer"


class OrgRole(StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Plan(StrEnum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class Provider(StrEnum):
    github = "github"
    gitlab = "gitlab"


class PRState(StrEnum):
    open = "open"
    closed = "closed"
    merged = "merged"


class ReviewSessionStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class AICategory(StrEnum):
    bug = "bug"
    style = "style"
    security = "security"
    performance = "performance"
    tests = "tests"
    docs = "docs"


class ReviewAction(StrEnum):
    viewed = "viewed"
    commented = "commented"
    approved = "approved"
    requested_changes = "requested_changes"
