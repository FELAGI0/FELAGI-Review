"""initial schema

Revision ID: 97d41c34ddfd
Revises:
Create Date: 2026-09-29 03:09:44.711186

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "97d41c34ddfd"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str] | None] = None
depends_on: Union[str, Sequence[str] | None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("github_id", sa.BigInteger(), nullable=True),
        sa.Column("role", sa.Enum("admin", "reviewer", "viewer", name="userrole"), nullable=False),
        sa.Column("review_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("github_id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("plan", sa.Enum("free", "pro", "enterprise", name="plan"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="orgrole"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "repositories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Enum("github", "gitlab", name="provider"), nullable=False),
        sa.Column("external_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("webhook_secret", sa.String(), nullable=True),
        sa.Column("access_token_encrypted", sa.String(), nullable=True),
        sa.Column("auto_review_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("repo_id", sa.UUID(), nullable=False),
        sa.Column("enabled_checks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("custom_rules", sa.Text(), nullable=True),
        sa.Column("ignore_paths", sa.ARRAY(sa.String()), nullable=False),
        sa.Column(
            "severity_threshold",
            sa.Enum("info", "warning", "error", "critical", name="severity"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id"),
    )
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("repo_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.BigInteger(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author_login", sa.String(), nullable=False),
        sa.Column("base_branch", sa.String(), nullable=False),
        sa.Column("head_branch", sa.String(), nullable=False),
        sa.Column("state", sa.Enum("open", "closed", "merged", name="prstate"), nullable=False),
        sa.Column("additions", sa.Integer(), nullable=False),
        sa.Column("deletions", sa.Integer(), nullable=False),
        sa.Column("files_changed", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "number"),
    )
    op.create_table(
        "comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("pr_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"]),
        sa.ForeignKeyConstraint(["pr_id"], ["pull_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review_activity",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("pr_id", sa.UUID(), nullable=False),
        sa.Column(
            "action",
            sa.Enum(
                "viewed",
                "commented",
                "approved",
                "requested_changes",
                name="reviewaction",
            ),
            nullable=False,
        ),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pr_id"], ["pull_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("pr_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="reviewsessionstatus"),
            nullable=False,
        ),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["pr_id"], ["pull_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column(
            "severity",
            sa.Enum("info", "warning", "error", "critical", name="severity"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "bug",
                "style",
                "security",
                "performance",
                "tests",
                "docs",
                name="aicategory",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("code_snippet", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["review_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("comment_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("comment_id", "user_id", "emoji"),
    )

    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_memberships_org_id", "memberships", ["org_id"])
    op.create_index("ix_repositories_org_id", "repositories", ["org_id"])
    op.create_index("ix_ai_settings_repo_id", "ai_settings", ["repo_id"])
    op.create_index("ix_pr_repo_state", "pull_requests", ["repo_id", "state"])
    op.create_index("ix_pull_requests_repo_id", "pull_requests", ["repo_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_pr_id", "comments", ["pr_id"])
    op.create_index("ix_comments_pr_file_line", "comments", ["pr_id", "file_path", "line_number"])
    op.create_index("ix_review_activity_user_created", "review_activity", ["user_id", "created_at"])
    op.create_index("ix_review_activity_pr_id", "review_activity", ["pr_id"])
    op.create_index("ix_review_sessions_pr_id", "review_sessions", ["pr_id"])
    op.create_index("ix_ai_comments_session_id", "ai_comments", ["session_id"])
    op.create_index("ix_reactions_comment_id", "reactions", ["comment_id"])
    op.create_index("ix_reactions_user_id", "reactions", ["user_id"])
    op.execute(
        "CREATE INDEX ix_ai_comments_embedding ON ai_comments "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("reactions")
    op.drop_table("ai_comments")
    op.drop_table("review_sessions")
    op.drop_table("review_activity")
    op.drop_table("comments")
    op.drop_table("pull_requests")
    op.drop_table("ai_settings")
    op.drop_table("repositories")
    op.drop_table("memberships")
    op.drop_table("organizations")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS orgrole")
    op.execute("DROP TYPE IF EXISTS plan")
    op.execute("DROP TYPE IF EXISTS provider")
    op.execute("DROP TYPE IF EXISTS severity")
    op.execute("DROP TYPE IF EXISTS prstate")
    op.execute("DROP TYPE IF EXISTS reviewaction")
    op.execute("DROP TYPE IF EXISTS reviewsessionstatus")
    op.execute("DROP TYPE IF EXISTS aicategory")
    op.execute("DROP EXTENSION IF EXISTS vector")
