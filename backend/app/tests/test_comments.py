from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Comment, Organization, PullRequest, Repository, User
from app.security import create_access_token


def _run_id() -> str:
    return uuid4().hex[:8]


RUN = _run_id()
TEST_USER_ID = uuid4()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(TEST_USER_ID))}"}


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def other_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(uuid4()))}"}


@pytest.fixture
async def db_session():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import settings

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture(autouse=True)
async def reset_app_engine():
    from app.db import session as db_session_module

    await db_session_module.engine.dispose()
    yield
    await db_session_module.engine.dispose()


async def _setup_pr(db: AsyncSession) -> PullRequest:
    user = User(
        id=uuid4(),
        email=f"pr-author-{RUN}@example.com",
        username=f"pr-author-{RUN}",
        github_id=700_000_000 + int(RUN[:6], 16),
    )
    db.add(user)
    token_user = User(
        id=TEST_USER_ID,
        email=f"commenter-{RUN}@example.com",
        username=f"commenter-{RUN}",
        github_id=710_000_000 + int(RUN[:6], 16),
    )
    db.add(token_user)
    await db.flush()
    org = Organization(
        id=uuid4(),
        name=f"org-{RUN}",
        slug=f"org-{RUN}",
        owner_id=user.id,
    )
    db.add(org)
    await db.flush()
    repo = Repository(
        id=uuid4(),
        org_id=org.id,
        external_id=800_000_000 + int(RUN[:6], 16),
        github_id=800_000_000 + int(RUN[:6], 16),
        installation_id=1,
        full_name=f"org-{RUN}/repo",
    )
    db.add(repo)
    await db.flush()
    pr = PullRequest(
        id=uuid4(),
        repo_id=repo.id,
        external_id=900_000_000 + int(RUN[:6], 16),
        github_id=900_000_000 + int(RUN[:6], 16),
        number=1,
        title="Test PR",
        author_login="author",
        base_branch="main",
        head_branch="feature",
    )
    db.add(pr)
    await db.commit()
    return pr


@pytest.fixture
async def test_pr(db_session):
    pr = await _setup_pr(db_session)
    yield pr
    await db_session.execute(
        delete(Comment).where(Comment.pr_id == pr.id)
    )
    await db_session.execute(delete(PullRequest).where(PullRequest.id == pr.id))
    await db_session.execute(delete(Repository).where(Repository.id == pr.repo_id))
    await db_session.execute(delete(Organization).where(Organization.slug == f"org-{RUN}"))
    await db_session.execute(delete(User).where(User.github_id == 700_000_000 + int(RUN[:6], 16)))
    await db_session.execute(delete(User).where(User.id == TEST_USER_ID))
    await db_session.commit()


def test_list_comments_requires_auth(client: TestClient) -> None:
    response = client.get(f"/api/prs/{uuid4()}/comments")
    assert response.status_code == 401


async def test_list_comments_empty(client: TestClient, auth_headers: dict, test_pr) -> None:
    response = client.get(f"/api/prs/{test_pr.id}/comments", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_create_and_list_comment(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    create = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Looks good", "file_path": "src/app.py", "line_number": 12},
        headers=auth_headers,
    )
    assert create.status_code == 201
    created = create.json()
    assert created["body"] == "Looks good"
    assert created["file_path"] == "src/app.py"
    assert created["line_number"] == 12
    assert created["resolved"] is False
    assert created["parent_id"] is None

    listing = client.get(f"/api/prs/{test_pr.id}/comments", headers=auth_headers)
    assert listing.status_code == 200
    threads = listing.json()
    assert len(threads) == 1
    assert threads[0]["root"]["id"] == created["id"]
    assert threads[0]["replies"] == []


async def test_create_reply_and_thread_structure(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    root = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Root comment"},
        headers=auth_headers,
    ).json()

    reply = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Reply", "parent_id": root["id"]},
        headers=auth_headers,
    )
    assert reply.status_code == 201

    reply2 = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Reply to reply", "parent_id": reply.json()["id"]},
        headers=auth_headers,
    )
    assert reply2.status_code == 400

    threads = client.get(
        f"/api/prs/{test_pr.id}/comments", headers=auth_headers
    ).json()
    assert len(threads) == 1
    assert threads[0]["root"]["id"] == root["id"]
    assert [r["body"] for r in threads[0]["replies"]] == ["Reply"]


async def test_reply_from_other_pr_rejected(
    client: TestClient, auth_headers: dict, test_pr, db_session
) -> None:
    other_pr = await _setup_pr_other(db_session)
    root = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Root"},
        headers=auth_headers,
    ).json()
    reply = client.post(
        f"/api/prs/{other_pr.id}/comments",
        json={"body": "Bad reply", "parent_id": root["id"]},
        headers=auth_headers,
    )
    assert reply.status_code == 400

    await _cleanup_pr(db_session, other_pr)


async def test_update_comment(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    comment = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Original"},
        headers=auth_headers,
    ).json()

    patched = client.patch(
        f"/api/comments/{comment['id']}",
        json={"body": "Edited"},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["body"] == "Edited"
    assert patched.json()["updated_at"] >= patched.json()["created_at"]


async def test_update_other_users_comment_forbidden(
    client: TestClient, auth_headers: dict, other_auth_headers: dict, test_pr
) -> None:
    comment = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Someone else's"},
        headers=auth_headers,
    ).json()

    patched = client.patch(
        f"/api/comments/{comment['id']}",
        json={"body": "Hijack"},
        headers=other_auth_headers,
    )
    assert patched.status_code == 403


async def test_delete_comment(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    comment = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "To delete"},
        headers=auth_headers,
    ).json()

    deleted = client.delete(f"/api/comments/{comment['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    listing = client.get(f"/api/prs/{test_pr.id}/comments", headers=auth_headers)
    assert listing.json() == []


async def test_delete_comment_promotes_replies_to_roots(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    root = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Root"},
        headers=auth_headers,
    ).json()
    reply = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Reply", "parent_id": root["id"]},
        headers=auth_headers,
    ).json()

    client.delete(f"/api/comments/{root['id']}", headers=auth_headers)

    threads = client.get(f"/api/prs/{test_pr.id}/comments", headers=auth_headers).json()
    assert len(threads) == 1
    assert threads[0]["root"]["id"] == reply["id"]
    assert threads[0]["root"]["parent_id"] is None


async def test_resolve_toggle(
    client: TestClient, auth_headers: dict, test_pr
) -> None:
    comment = client.post(
        f"/api/prs/{test_pr.id}/comments",
        json={"body": "Resolve me"},
        headers=auth_headers,
    ).json()

    resolved = client.post(
        f"/api/comments/{comment['id']}/resolve", headers=auth_headers
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved"] is True

    unresolved = client.post(
        f"/api/comments/{comment['id']}/resolve", headers=auth_headers
    )
    assert unresolved.json()["resolved"] is False


def test_create_comment_unknown_pr(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        f"/api/prs/{uuid4()}/comments",
        json={"body": "No PR"},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def _setup_pr_other(db: AsyncSession) -> PullRequest:
    result = await db.execute(
        select(PullRequest).where(PullRequest.github_id == 900_000_000 + int(RUN[:6], 16))
    )
    existing = result.scalar_one()
    pr = PullRequest(
        id=uuid4(),
        repo_id=existing.repo_id,
        external_id=910_000_000 + int(RUN[:6], 16),
        github_id=910_000_000 + int(RUN[:6], 16),
        number=2,
        title="Other PR",
        author_login="author",
        base_branch="main",
        head_branch="feature2",
    )
    db.add(pr)
    await db.commit()
    return pr


async def _cleanup_pr(db: AsyncSession, pr: PullRequest) -> None:
    await db.execute(delete(Comment).where(Comment.pr_id == pr.id))
    await db.execute(delete(PullRequest).where(PullRequest.id == pr.id))
    await db.commit()
