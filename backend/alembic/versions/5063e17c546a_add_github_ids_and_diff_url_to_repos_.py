"""add github ids and diff url to repos and pull requests

Revision ID: 5063e17c546a
Revises: 97d41c34ddfd
Create Date: 2026-10-27 19:23:26.624406

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "5063e17c546a"
down_revision: Union[str, None] = "97d41c34ddfd"
branch_labels: Union[str, Sequence[str] | None] = None
depends_on: Union[str, Sequence[str] | None] = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("github_id", sa.BigInteger(), nullable=True))
    op.add_column("repositories", sa.Column("installation_id", sa.BigInteger(), nullable=True))
    op.add_column("pull_requests", sa.Column("github_id", sa.BigInteger(), nullable=True))
    op.add_column("pull_requests", sa.Column("diff_url", sa.String(), nullable=True))
    op.create_unique_constraint("uq_repositories_github_id", "repositories", ["github_id"])
    op.create_unique_constraint("uq_pull_requests_github_id", "pull_requests", ["github_id"])


def downgrade() -> None:
    op.drop_constraint("uq_pull_requests_github_id", "pull_requests")
    op.drop_constraint("uq_repositories_github_id", "repositories")
    op.drop_column("pull_requests", "diff_url")
    op.drop_column("pull_requests", "github_id")
    op.drop_column("repositories", "installation_id")
    op.drop_column("repositories", "github_id")
