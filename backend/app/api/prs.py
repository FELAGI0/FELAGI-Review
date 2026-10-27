from datetime import datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import PullRequest, Repository
from app.models.base import PRState
from app.security import get_current_user
from app.services.diff_parser import parse_diff
from app.services.github_app import GitHubAppClient, GitHubAppError

router = APIRouter(dependencies=[Depends(get_current_user)])


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    github_id: int | None = None
    installation_id: int | None = None
    auto_review_enabled: bool


class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repo_id: str
    github_id: int | None = None
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
    diff_url: str | None = None
    created_at: datetime
    updated_at: datetime


class DiffFileOut(BaseModel):
    path: str
    old_path: str = Field(alias="old_path")
    status: str
    additions: int
    deletions: int
    is_binary: bool
    hunks: list[dict]


async def _get_repo_or_404(db: AsyncSession, repo_id: str) -> Repository:
    try:
        repo_uuid = UUID(repo_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid repository id") from exc
    result = await db.execute(select(Repository).where(Repository.id == repo_uuid))
    repository = result.scalar_one_or_none()
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@router.get("/repositories")
async def list_repositories(db: AsyncSession = Depends(get_db)) -> list[RepositoryOut]:
    result = await db.execute(select(Repository).order_by(Repository.full_name))
    return [
        RepositoryOut.model_validate(
            {
                "id": str(repo.id),
                "full_name": repo.full_name,
                "github_id": repo.github_id,
                "installation_id": repo.installation_id,
                "auto_review_enabled": repo.auto_review_enabled,
            }
        )
        for repo in result.scalars()
    ]


@router.get("/repositories/{repo_id}/pulls")
async def list_pull_requests(
    repo_id: str,
    state: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PullRequestOut]:
    repository = await _get_repo_or_404(db, repo_id)
    query = select(PullRequest).where(PullRequest.repo_id == repository.id)
    if state in ("open", "closed", "merged"):
        query = query.where(PullRequest.state == PRState(state))
    query = query.order_by(PullRequest.updated_at.desc())
    result = await db.execute(query)
    return [PullRequestOut.model_validate(pr) for pr in result.scalars()]


@router.get("/repositories/{repo_id}/pulls/{number}")
async def get_pull_request(
    repo_id: str,
    number: int,
    db: AsyncSession = Depends(get_db),
) -> PullRequestOut:
    repository = await _get_repo_or_404(db, repo_id)
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.repo_id == repository.id, PullRequest.number == number
        )
    )
    pr = result.scalar_one_or_none()
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return PullRequestOut.model_validate(pr)


@router.get("/repositories/{repo_id}/pulls/{number}/diff")
async def get_pull_request_diff(
    repo_id: str,
    number: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repository = await _get_repo_or_404(db, repo_id)
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.repo_id == repository.id, PullRequest.number == number
        )
    )
    pr = result.scalar_one_or_none()
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    if not pr.diff_url:
        raise HTTPException(status_code=404, detail="Diff URL is not available for this PR")

    diff_text = await _fetch_diff(pr.diff_url, repository.installation_id)
    return {
        "pull_number": number,
        "files": parse_diff(diff_text),
    }


async def _fetch_diff(diff_url: str, installation_id: int | None) -> str:
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if installation_id:
        app_client = GitHubAppClient()
        try:
            token = await app_client.get_installation_token(installation_id)
            headers["Authorization"] = f"Bearer {token}"
        except GitHubAppError:
            pass
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(diff_url, headers=headers, timeout=30.0)
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch diff from GitHub: {response.status_code}",
        )
    return response.text


@router.get("/github-app/install-url")
async def github_app_install_url() -> dict:
    if not settings.github_app_id:
        raise HTTPException(status_code=503, detail="GitHub App is not configured")
    return {"install_url": "https://github.com/apps/felagi-review-app/installations/new"}
