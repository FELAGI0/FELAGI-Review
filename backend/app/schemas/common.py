from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import AICategory, Plan, Provider, PRState, Severity


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    avatar_url: str | None = None
    role: str
    review_score: int
    created_at: datetime


class OrganizationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    owner_id: UUID
    plan: Plan
    created_at: datetime


class RepositorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    provider: Provider
    external_id: int
    full_name: str
    auto_review_enabled: bool
    created_at: datetime


class PullRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repo_id: UUID
    external_id: int
    number: int
    title: str
    description: str | None = None
    author_login: str
    base_branch: str
    head_branch: str
    state: PRState
    additions: int
    deletions: int
    files_changed: int
    created_at: datetime
    updated_at: datetime


class ReviewSessionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pr_id: UUID
    status: str
    model_used: str | None = None
    tokens_used: int
    cost_usd: float
    summary: str | None = None
    risk_score: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AICommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    severity: Severity
    category: AICategory
    message: str
    suggestion: str | None = None
    code_snippet: str | None = None
    is_resolved: bool
    is_dismissed: bool
    created_at: datetime


class CommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pr_id: UUID
    user_id: UUID
    parent_id: UUID | None = None
    file_path: str | None = None
    line_number: int | None = None
    body: str
    resolved: bool
    created_at: datetime
    updated_at: datetime
