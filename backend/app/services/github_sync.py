from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import logger
from app.models import Organization, PullRequest, Repository
from app.models.base import Provider, PRState


def _pr_state(payload_pr: dict[str, Any]) -> PRState:
    if payload_pr.get("merged"):
        return PRState.merged
    if payload_pr.get("state") == "closed":
        return PRState.closed
    return PRState.open


def _installation_id(payload: dict[str, Any]) -> int | None:
    installation = payload.get("installation")
    if isinstance(installation, dict):
        return installation.get("id")
    return None


async def sync_installation_repos(db: AsyncSession, payload: dict[str, Any]) -> list[Repository]:
    """Save repositories attached to a fresh app installation."""
    installation_id = _installation_id(payload)
    repositories = payload.get("repositories") or []
    if not installation_id or not repositories:
        return []

    account = (payload.get("installation") or {}).get("account") or {}
    org_name = account.get("login") or "default"
    org = await _get_or_create_org(db, org_name)

    saved: list[Repository] = []
    for repo in repositories:
        github_id = repo.get("id")
        if github_id is None:
            continue
        repository = await _upsert_repository(db, org.id, github_id, repo, installation_id)
        saved.append(repository)
    await db.commit()
    logger.info(
        "installation_repos_synced",
        org=org_name,
        installation_id=installation_id,
        repos=[r.full_name for r in saved],
    )
    return saved


async def sync_pull_request(db: AsyncSession, payload: dict[str, Any]) -> PullRequest | None:
    """Create or update a pull_requests row from a webhook payload."""
    repo = payload.get("repository") or {}
    github_id = repo.get("id")
    if github_id is None:
        return None
    result = await db.execute(select(Repository).where(Repository.github_id == github_id))
    repository = result.scalar_one_or_none()
    if repository is None:
        logger.info("webhook_repo_not_found", github_id=github_id, repo=repo.get("full_name"))
        return None

    pr_payload = payload.get("pull_request") or {}
    number = pr_payload.get("number")
    if number is None:
        return None

    pr_state = _pr_state(pr_payload)
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.repo_id == repository.id, PullRequest.number == number
        )
    )
    pull_request = result.scalar_one_or_none()

    values = {
        "github_id": pr_payload.get("id"),
        "title": pr_payload.get("title") or "",
        "description": pr_payload.get("body"),
        "author_login": (pr_payload.get("user") or {}).get("login") or "unknown",
        "base_branch": (pr_payload.get("base") or {}).get("ref") or "unknown",
        "head_branch": (pr_payload.get("head") or {}).get("ref") or "unknown",
        "state": pr_state,
        "additions": pr_payload.get("additions") or 0,
        "deletions": pr_payload.get("deletions") or 0,
        "files_changed": pr_payload.get("changed_files") or 0,
        "diff_url": pr_payload.get("diff_url"),
    }
    if pull_request is None:
        pull_request = PullRequest(
            id=uuid4(),
            repo_id=repository.id,
            external_id=pr_payload.get("id") or 0,
            number=number,
            **values,
        )
        db.add(pull_request)
    else:
        for field, value in values.items():
            setattr(pull_request, field, value)
    await db.commit()
    logger.info(
        "pr_synced",
        repo=repository.full_name,
        number=number,
        state=pr_state.value,
        github_pr_id=values["github_id"],
    )
    return pull_request


async def _get_or_create_org(db: AsyncSession, name: str) -> Organization:
    slug = name.lower()
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    org = result.scalar_one_or_none()
    if org is not None:
        return org
    org = Organization(id=uuid4(), name=name, slug=slug, owner_id=await _default_owner_id(db))
    db.add(org)
    await db.flush()
    return org


async def _default_owner_id(db: AsyncSession):
    from app.models import User

    result = await db.execute(select(User).order_by(User.created_at).limit(1))
    user = result.scalar_one_or_none()
    if user is not None:
        return user.id
    raise ValueError("No users found to own the organization")


async def _upsert_repository(
    db: AsyncSession,
    org_id,
    github_id: int,
    repo: dict[str, Any],
    installation_id: int | None,
) -> Repository:
    result = await db.execute(select(Repository).where(Repository.github_id == github_id))
    repository = result.scalar_one_or_none()
    full_name = repo.get("full_name") or repo.get("name") or str(github_id)
    if repository is None:
        repository = Repository(
            id=uuid4(),
            org_id=org_id,
            provider=Provider.github,
            external_id=github_id,
            github_id=github_id,
            installation_id=installation_id,
            full_name=full_name,
        )
        db.add(repository)
    else:
        repository.org_id = org_id
        repository.installation_id = installation_id
        repository.full_name = full_name
    await db.flush()
    return repository
