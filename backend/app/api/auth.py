from datetime import UTC, datetime
from uuid import UUID, uuid4

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.security import create_access_token, create_refresh_token, get_current_user
from app.services.github_oauth import GitHubOAuthClient, GitHubOAuthError

router = APIRouter()

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


@router.get("/auth/github/login")
async def github_login() -> RedirectResponse:
    state = str(uuid4())
    await redis_client.set(f"github_oauth_state:{state}", "1", ex=600)
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri or "",
        "scope": "read:user user:email",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{settings.github_oauth_authorize_url}?{query}")


@router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    redis_key = f"github_oauth_state:{state}"
    if not await redis_client.exists(redis_key):
        raise HTTPException(status_code=400, detail="Invalid state")
    await redis_client.delete(redis_key)

    client = GitHubOAuthClient()
    try:
        access_token = await client.exchange_code_for_token(code)
        gh_user = await client.get_user(access_token)
        email = await client.get_primary_email(access_token)
    except GitHubOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await db.execute(select(User).where(User.github_id == gh_user["id"]))
    user = result.scalar_one_or_none()
    if user:
        user.username = gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
        user.email = email
    else:
        user = User(
            id=uuid4(),
            email=email,
            username=gh_user["login"],
            avatar_url=gh_user.get("avatar_url"),
            github_id=gh_user["id"],
        )
        db.add(user)
    await db.commit()

    jwt_access = create_access_token(str(user.id))
    jwt_refresh = create_refresh_token(str(user.id))
    response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={jwt_access}"
    )
    response.set_cookie(
        key="refresh_token",
        value=jwt_refresh,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/api/auth",
    )
    return response


@router.post("/auth/refresh")
async def refresh(request: Request) -> dict[str, str]:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    from app.security import decode_token

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await redis_client.exists(f"jwt_blacklist:{jti}"):
        raise HTTPException(status_code=401, detail="Token revoked")

    access = create_access_token(payload["sub"])
    return {"access_token": access}


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, response: Response) -> Response:
    token = request.cookies.get("refresh_token")
    if token:
        from app.security import decode_token

        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            if jti:
                ttl = int(payload.get("exp", 0) - datetime.now(UTC).timestamp())
                if ttl > 0:
                    await redis_client.setex(f"jwt_blacklist:{jti}", ttl, "1")
        except HTTPException:
            pass
    response.delete_cookie("refresh_token", path="/api/auth")
    return response


@router.get("/auth/me")
async def me(
    user_id: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(select(User).where(User.id == UUID(user_id["id"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "role": user.role.value,
        "review_score": user.review_score,
    }
