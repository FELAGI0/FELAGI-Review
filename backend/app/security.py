from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings

TOKEN_URL = "/api/auth/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL, auto_error=False)


def create_access_token(subject: str, expires_minutes: int = 15) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {"sub": subject, "type": "access", "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def create_refresh_token(subject: str, expires_days: int = 7) -> str:
    expire = datetime.now(UTC) + timedelta(days=expires_days)
    return jwt.encode(
        {"sub": subject, "type": "refresh", "jti": str(uuid4()), "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> dict[str, Any]:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": payload["sub"]}
