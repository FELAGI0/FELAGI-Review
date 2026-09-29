import httpx

from app.core.config import settings


class GitHubOAuthError(Exception):
    pass


class GitHubOAuthClient:
    def __init__(self) -> None:
        self._client_id = settings.github_client_id
        self._client_secret = settings.github_client_secret

    async def exchange_code_for_token(self, code: str) -> str:
        if not self._client_id or not self._client_secret:
            raise GitHubOAuthError("GitHub OAuth is not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.github_oauth_token_url,
                json={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": settings.github_redirect_uri,
                },
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
        response.raise_for_status()
        data = response.json()
        if "access_token" not in data:
            raise GitHubOAuthError(data.get("error_description", "token exchange failed"))
        return data["access_token"]

    async def get_user(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.github_api_base_url}/user",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
        response.raise_for_status()
        return response.json()

    async def get_primary_email(self, access_token: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.github_api_base_url}/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
        response.raise_for_status()
        emails = response.json()
        for email in emails:
            if email.get("primary") and email.get("verified"):
                return email["email"]
        raise GitHubOAuthError("No verified primary email")
