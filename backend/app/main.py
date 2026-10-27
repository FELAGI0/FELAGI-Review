from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, github_app, github_webhook, health, prs
from app.core.config import settings
from app.logging import logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    logger.info("startup", service=settings.service_name, env=settings.environment)
    yield


app = FastAPI(
    title="FELAGI-Review API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    structlog.contextvars.bind_contextvars(
        service=settings.service_name, request_id=request_id
    )
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.unbind_contextvars("request_id", "service")
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "Unexpected server error",
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["auth"])
app.include_router(github_app.router, prefix=settings.api_v1_prefix, tags=["github-app"])
app.include_router(
    github_webhook.router, prefix=settings.api_v1_prefix, tags=["github-webhook"]
)
app.include_router(prs.router, prefix=settings.api_v1_prefix, tags=["prs"])
app.include_router(health.router, tags=["health"])
