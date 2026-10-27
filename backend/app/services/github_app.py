import hashlib
import hmac
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from jose import jwt

from app.core.config import settings


class GitHubAppError(Exception):
    pass


class GitHubAppNotConfigured(GitHubAppError):
    pass


class WebhookSignatureError(GitHubAppError):
    pass


class GitHubAppClient:
    """Client for the GitHub App API: app JWT, installation tokens, webhooks."""

    def __init__(self) -> None:
        self._app_id = settings.github_app_id
        self._private_key_path = settings.github_app_private_key_path
        self._webhook_secret = settings.github_app_webhook_secret
        self._api_base_url = settings.github_api_base_url

    @property
    def configured(self) -> bool:
        return bool(self._app_id and self._private_key_path)

    def _load_private_key(self) -> RSAPrivateKey:
        if not self._private_key_path:
            raise GitHubAppNotConfigured("GitHub App private key path is not set")
        key_data = Path(self._private_key_path).read_bytes()
        try:
            key = serialization.load_pem_private_key(key_data, password=None)
        except ValueError as exc:
            raise GitHubAppError(f"Cannot load private key: {exc}") from exc
        if not isinstance(key, RSAPrivateKey):
            raise GitHubAppError("Private key is not an RSA key")
        return key

    def create_app_jwt(self) -> str:
        """Signed JWT authenticating as the GitHub App itself."""
        if not self._app_id or not self._private_key_path:
            raise GitHubAppNotConfigured("GitHub App is not configured")
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": str(self._app_id),
        }
        return jwt.encode(
            payload, self._load_private_key().private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            algorithm="RS256",
        )

    def verify_webhook_signature(self, payload_body: bytes, signature: str | None) -> None:
        """Verify the X-Hub-Signature-256 header of a webhook delivery."""
        if not self._webhook_secret:
            raise GitHubAppNotConfigured("Webhook secret is not set")
        if not signature:
            raise WebhookSignatureError("Missing signature header")
        expected = "sha256=" + hmac.new(
            self._webhook_secret.encode(), payload_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookSignatureError("Invalid signature")

    async def get_installation_token(self, installation_id: int) -> str:
        """Short-lived token acting on behalf of an app installation."""
        app_jwt = self.create_app_jwt()
        url = f"{self._api_base_url}/app/installations/{installation_id}/access_tokens"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {app_jwt}"},
                timeout=10.0,
            )
        if response.status_code != 201:
            raise GitHubAppError(
                f"Installation token request failed: {response.status_code} {response.text}"
            )
        return response.json()["token"]

    async def get_installations(self) -> list[dict]:
        """List of installations of the app (requires app JWT)."""
        app_jwt = self.create_app_jwt()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_base_url}/app/installations",
                headers={"Authorization": f"Bearer {app_jwt}"},
                timeout=10.0,
            )
        if response.status_code != 200:
            raise GitHubAppError(
                f"Installations request failed: {response.status_code} {response.text}"
            )
        return response.json()

    async def get_app_info(self) -> dict:
        """Public metadata about the app."""
        app_jwt = self.create_app_jwt()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_base_url}/app",
                headers={"Authorization": f"Bearer {app_jwt}"},
                timeout=10.0,
            )
        if response.status_code != 200:
            raise GitHubAppError(
                f"App info request failed: {response.status_code} {response.text}"
            )
        return response.json()


def installation_token_expiry(token_response: dict) -> datetime:
    expires_at = datetime.fromisoformat(token_response["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at - timedelta(minutes=5)
