import hashlib
import hmac
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Organization, PullRequest, Repository, User
from app.services.diff_parser import parse_diff

WEBHOOK_URL = "/api/webhooks/github"


def _run_id() -> str:
    return uuid4().hex[:8]


RUN = _run_id()


@pytest.fixture(autouse=True)
async def reset_app_engine():
    """Dispose the app-level engine so pooled connections never cross event loops."""
    from app.db import session as db_session_module

    await db_session_module.engine.dispose()
    yield
    await db_session_module.engine.dispose()

SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,4 +1,6 @@
 import os
+import httpx
+from fastapi import FastAPI

 def main():
diff --git a/README.md b/README.md
new file mode 100644
--- /dev/null
+++ b/README.md
@@ -0,0 +1,2 @@
+# Project
+Docs here.
"""


def _installation_payload() -> dict:
    return {
        "action": "created",
        "installation": {
            "id": 55_000_000 + int(RUN[:6], 16),
            "account": {"login": f"sync-{RUN}", "id": 424_242},
        },
        "repositories": [
            {"id": 100_000_001 + int(RUN[:6], 16), "name": "repo-one",
             "full_name": f"sync-{RUN}/repo-one"},
            {"id": 100_000_002 + int(RUN[:6], 16), "name": "repo-two",
             "full_name": f"sync-{RUN}/repo-two"},
        ],
    }


def _pr_payload(repo_id: int) -> dict:
    return {
        "action": "opened",
        "installation": {"id": 55_000_000 + int(RUN[:6], 16)},
        "repository": {"id": repo_id, "name": "repo-one", "full_name": "x/repo-one"},
        "pull_request": {
            "id": 900_000_001 + int(RUN[:6], 16),
            "number": 7,
            "title": "Add httpx client",
            "body": "Some body",
            "user": {"login": "someuser"},
            "base": {"ref": "main"},
            "head": {"ref": "feature/httpx"},
            "state": "open",
            "merged": False,
            "additions": 42,
            "deletions": 7,
            "changed_files": 2,
            "diff_url": f"https://example.com/{RUN}/pull/7.diff",
        },
    }


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def webhook_secret(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(
        "app.services.github_app.settings.github_app_webhook_secret", f"secret-{RUN}"
    )
    return f"secret-{RUN}"


@pytest.fixture
async def db_session():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import settings

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def test_user(db_session):
    user = User(
        id=uuid4(),
        email=f"sync-{RUN}@example.com",
        username=f"sync-user-{RUN}",
        github_id=999_000_000 + int(RUN[:6], 16),
    )
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.commit()


@pytest.fixture
async def cleanup(db_session):
    yield
    await db_session.execute(
        delete(PullRequest).where(
            PullRequest.github_id == 900_000_001 + int(RUN[:6], 16)
        )
    )
    await db_session.execute(
        delete(Repository).where(
            Repository.github_id.in_(
                [100_000_001 + int(RUN[:6], 16), 100_000_002 + int(RUN[:6], 16)]
            )
        )
    )
    await db_session.execute(
        delete(Organization).where(Organization.slug == f"sync-{RUN}")
    )
    await db_session.commit()


def _post_webhook(client: TestClient, event: str, payload: dict, secret: str):
    body = json.dumps(payload).encode()
    return client.post(
        WEBHOOK_URL,
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, secret),
            "X-GitHub-Event": event,
        },
    )


async def test_installation_created_syncs_repositories(
    client: TestClient, webhook_secret: str, db_session, test_user, cleanup
) -> None:
    payload = _installation_payload()
    response = _post_webhook(client, "installation", payload, webhook_secret)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "event": "installation", "repositories": 2}

    result = await db_session.execute(
        select(Repository).where(Repository.github_id == payload["repositories"][0]["id"])
    )
    repo_one = result.scalar_one()
    assert repo_one.full_name == payload["repositories"][0]["full_name"]
    assert repo_one.installation_id == payload["installation"]["id"]

    result = await db_session.execute(
        select(Repository).where(Repository.github_id == payload["repositories"][1]["id"])
    )
    assert result.scalar_one() is not None

    result = await db_session.execute(
        select(Organization).where(Organization.slug == f"sync-{RUN}")
    )
    org = result.scalar_one()
    assert repo_one.org_id == org.id


async def test_repositories_added_event_syncs(
    client: TestClient, webhook_secret: str, db_session, test_user, cleanup
) -> None:
    payload = {
        "action": "added",
        "installation": {
            "id": 56_000_000 + int(RUN[:6], 16),
            "account": {"login": f"sync-{RUN}"},
        },
        "repositories_added": [
            {"id": 200_000_001 + int(RUN[:6], 16), "name": "repo-three",
             "full_name": f"sync-{RUN}/repo-three"},
        ],
        "sender": {"login": "someuser"},
    }
    response = _post_webhook(client, "installation_repositories", payload, webhook_secret)
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "event": "installation_repositories",
        "repositories": 1,
    }

    result = await db_session.execute(
        select(Repository).where(
            Repository.github_id == payload["repositories_added"][0]["id"]
        )
    )
    repo = result.scalar_one()
    assert repo.full_name == f"sync-{RUN}/repo-three"
    assert repo.installation_id == payload["installation"]["id"]


async def test_pull_request_webhook_creates_record(
    client: TestClient, webhook_secret: str, db_session, test_user, cleanup
) -> None:
    installation = _installation_payload()
    _post_webhook(client, "installation", installation, webhook_secret)

    payload = _pr_payload(installation["repositories"][0]["id"])
    response = _post_webhook(client, "pull_request", payload, webhook_secret)
    assert response.status_code == 200
    assert response.json()["synced"] is True
    assert response.json()["pr_number"] == 7

    result = await db_session.execute(
        select(PullRequest).where(
            PullRequest.github_id == payload["pull_request"]["id"]
        )
    )
    pr = result.scalar_one()
    assert pr.number == 7
    assert pr.title == "Add httpx client"
    assert pr.author_login == "someuser"
    assert pr.base_branch == "main"
    assert pr.head_branch == "feature/httpx"
    assert pr.state.value == "open"
    assert pr.additions == 42
    assert pr.deletions == 7
    assert pr.files_changed == 2
    assert pr.diff_url == payload["pull_request"]["diff_url"]


async def test_pull_request_webhook_updates_existing(
    client: TestClient, webhook_secret: str, db_session, test_user, cleanup
) -> None:
    installation = _installation_payload()
    _post_webhook(client, "installation", installation, webhook_secret)
    payload = _pr_payload(installation["repositories"][0]["id"])
    _post_webhook(client, "pull_request", payload, webhook_secret)

    updated = {
        **payload,
        "action": "synchronize",
        "pull_request": {**payload["pull_request"], "additions": 50, "deletions": 10},
    }
    response = _post_webhook(client, "pull_request", updated, webhook_secret)
    assert response.status_code == 200

    result = await db_session.execute(
        select(PullRequest).where(
            PullRequest.github_id == payload["pull_request"]["id"]
        )
    )
    pr = result.scalar_one()
    assert pr.additions == 50
    assert pr.deletions == 10


async def test_pr_webhook_unknown_repo_not_synced(
    client: TestClient, webhook_secret: str, db_session, test_user, cleanup
) -> None:
    payload = _pr_payload(77_777_777)
    response = _post_webhook(client, "pull_request", payload, webhook_secret)
    assert response.status_code == 200
    assert response.json()["synced"] is False


def test_parse_diff_basic() -> None:
    files = parse_diff(SAMPLE_DIFF)
    assert len(files) == 2

    app_py = files[0]
    assert app_py["path"] == "src/app.py"
    assert app_py["status"] == "modified"
    assert app_py["additions"] == 2
    assert app_py["deletions"] == 0
    assert len(app_py["hunks"]) == 1
    add_lines = [line for line in app_py["hunks"][0]["lines"] if line["type"] == "add"]
    assert len(add_lines) == 2
    assert add_lines[0]["content"] == "import httpx"
    assert add_lines[0]["new_number"] == 2

    readme = files[1]
    assert readme["path"] == "README.md"
    assert readme["status"] == "added"
    assert readme["additions"] == 2
    assert readme["hunks"][0]["new_start"] == 1


def test_parse_diff_empty() -> None:
    assert parse_diff("") == []


def test_parse_diff_deleted_and_binary() -> None:
    diff = (
        "diff --git a/old.txt b/old.txt\n"
        "deleted file mode 100644\n"
        "--- a/old.txt\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        "-gone\n"
        "diff --git a/logo.png b/logo.png\n"
        "Binary files a/logo.png and b/logo.png differ\n"
    )
    files = parse_diff(diff)
    assert files[0]["status"] == "deleted"
    assert files[0]["deletions"] == 1
    assert files[1]["is_binary"] is True
    assert files[1]["hunks"] == []


def test_parse_diff_line_numbers() -> None:
    diff = (
        "diff --git a/f b/f\n"
        "--- a/f\n"
        "+++ b/f\n"
        "@@ -3,3 +3,3 @@\n"
        " ctx\n"
        "-old\n"
        "+new\n"
        " ctx2\n"
    )
    files = parse_diff(diff)
    lines = files[0]["hunks"][0]["lines"]
    assert lines[0]["type"] == "context" and lines[0]["old_number"] == 3
    assert lines[1]["type"] == "del" and lines[1]["old_number"] == 4
    assert lines[2]["type"] == "add" and lines[2]["new_number"] == 4
    assert lines[3]["type"] == "context" and lines[3]["new_number"] == 5
