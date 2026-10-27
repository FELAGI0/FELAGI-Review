import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import create_access_token
from app.services.github_app import (
    GitHubAppClient,
    GitHubAppNotConfigured,
    WebhookSignatureError,
)

WEBHOOK_URL = "/api/webhooks/github"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token("test-user")
    return {"Authorization": f"Bearer {token}"}


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_rejects_missing_signature(client: TestClient) -> None:
    response = client.post(WEBHOOK_URL, content=b"{}")
    assert response.status_code == 200
    assert response.json() == {"error": "invalid_signature"}


def test_webhook_rejects_bad_signature(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.github_app.settings.github_app_webhook_secret", "sec")
    response = client.post(
        WEBHOOK_URL,
        content=b'{"action": "opened"}',
        headers={"X-Hub-Signature-256": "sha256=deadbeef", "X-GitHub-Event": "pull_request"},
    )
    assert response.status_code == 200
    assert response.json() == {"error": "invalid_signature"}


def test_webhook_accepts_valid_signature(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.github_app.settings.github_app_webhook_secret", "sec")
    body = b'{"action": "opened"}'
    response = client.post(
        WEBHOOK_URL,
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, "sec"),
            "X-GitHub-Event": "pull_request",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "event": "pull_request"}


def test_webhook_installation_event(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.github_app.settings.github_app_webhook_secret", "sec")
    body = b'{"action": "created", "installation": {"id": 42}}'
    response = client.post(
        WEBHOOK_URL,
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, "sec"),
            "X-GitHub-Event": "installation",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "event": "installation"}


def test_github_app_status_requires_auth(client: TestClient) -> None:
    response = client.get("/api/github-app/status")
    assert response.status_code == 401


def test_github_app_status_not_configured(
    client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.github_app.settings.github_app_id", None)
    response = client.get("/api/github-app/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"configured": False}


def test_webhook_signature_verification_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.github_app.settings.github_app_webhook_secret", None)
    client = GitHubAppClient()
    pytest.raises(GitHubAppNotConfigured, client.verify_webhook_signature, b"x", "sha256=ab")
    client._webhook_secret = "sec"
    pytest.raises(WebhookSignatureError, client.verify_webhook_signature, b"x", None)
    good = "sha256=" + hmac.new(b"sec", b"x", hashlib.sha256).hexdigest()
    client.verify_webhook_signature(b"x", good)
    pytest.raises(WebhookSignatureError, client.verify_webhook_signature, b"y", good)
