from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.security import get_current_user

router = APIRouter()


@router.get("/auth/github/login")
async def github_login() -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "GitHub OAuth is not configured. "
                "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
            ),
        )
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri or "",
        "scope": "read:user user:email repo",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{settings.github_oauth_authorize_url}?{query}")


@router.get("/auth/github/callback")
async def github_callback(request: Request) -> dict[str, str]:
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    # TODO: exchange code for access token and upsert user; Phase 1 skeleton.
    return {"message": "GitHub callback received", "code": code}


@router.post("/auth/logout")
async def logout() -> dict[str, str]:
    return {"message": "Logged out"}


@router.get("/auth/me")
async def me(current_user: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": current_user}
