from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.security import get_current_user
from app.services.github_app import (
    GitHubAppClient,
    GitHubAppError,
    GitHubAppNotConfigured,
)

router = APIRouter()


@router.get("/github-app/status")
async def github_app_status(_: dict = Depends(get_current_user)) -> dict:
    client = GitHubAppClient()
    if not client.configured:
        return {"configured": False}
    status: dict = {
        "configured": True,
        "app_id": settings.github_app_id,
        "client_id": settings.github_app_client_id,
        "installations": None,
    }
    try:
        installations = await client.get_installations()
        status["installations"] = len(installations)
    except GitHubAppError as exc:
        status["installations_error"] = str(exc)
    return status


@router.post("/github-app/installations/{installation_id}/sync")
async def sync_installation(
    installation_id: int,
    _: dict = Depends(get_current_user),
) -> dict:
    client = GitHubAppClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="GitHub App is not configured")
    try:
        token = await client.get_installation_token(installation_id)
    except GitHubAppNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GitHubAppError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"installation_id": installation_id, "token_ok": bool(token)}
