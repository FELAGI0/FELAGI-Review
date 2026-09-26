import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import create_access_token


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_requires_auth(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    token = create_access_token("octocat")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "octocat"


def test_github_login_not_configured(client: TestClient) -> None:
    response = client.get("/api/auth/github/login")
    assert response.status_code == 503
