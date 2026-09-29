from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import create_refresh_token, decode_token


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_me_requires_auth(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_type(client: TestClient) -> None:
    refresh = create_refresh_token(str(uuid4()))
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {refresh}"}
    )
    assert response.status_code == 401


def test_refresh_missing_cookie(client: TestClient) -> None:
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_refresh_valid_cookie(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = str(uuid4())
    refresh = create_refresh_token(user_id)

    async def fake_exists(key: str) -> bool:
        return False

    monkeypatch.setattr("app.api.auth.redis_client.exists", fake_exists)
    client.cookies.set("refresh_token", refresh)
    response = client.post("/api/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()
    payload = decode_token(response.json()["access_token"])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_refresh_blacklisted_jti(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    refresh = create_refresh_token(str(uuid4()))

    async def fake_exists(key: str) -> bool:
        return True

    monkeypatch.setattr("app.api.auth.redis_client.exists", fake_exists)
    client.cookies.set("refresh_token", refresh)
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_login_saves_state_in_redis(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved_keys: list[str] = []

    async def fake_set(key: str, value: str, ex: int) -> bool:
        saved_keys.append(key)
        return True

    monkeypatch.setattr("app.api.auth.redis_client.set", fake_set)
    monkeypatch.setattr("app.core.config.settings.github_client_id", "test-id")
    response = client.get("/api/auth/github/login", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert len(saved_keys) == 1
    assert "github_oauth_state:" in saved_keys[0]
