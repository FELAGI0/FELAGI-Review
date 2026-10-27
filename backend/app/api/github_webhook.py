from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.logging import logger
from app.services.github_app import GitHubAppClient, WebhookSignatureError
from app.services.github_sync import (
    sync_installation_repos,
    sync_pull_request,
    sync_repositories_added,
)

router = APIRouter()

PR_ACTIONS = {"opened", "synchronize", "reopened", "closed"}


@router.post("/webhooks/github", status_code=200)
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    payload_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    event = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")

    client = GitHubAppClient()
    try:
        client.verify_webhook_signature(payload_body, signature)
    except WebhookSignatureError as exc:
        logger.warning(
            "webhook_rejected",
            gh_event=event,
            delivery_id=delivery_id,
            reason=str(exc),
        )
        return {"error": "invalid_signature"}

    payload: dict[str, Any] = await request.json()
    action = payload.get("action", "")
    logger.info(
        "webhook_received",
        gh_event=event,
        action=action,
        delivery_id=delivery_id,
        sender=(payload.get("sender") or {}).get("login"),
    )

    if event == "installation" and action == "created":
        saved = await sync_installation_repos(db, payload)
        return {"ok": True, "event": event, "repositories": len(saved)}

    if event == "installation_repositories" and action == "added":
        saved = await sync_repositories_added(db, payload)
        return {"ok": True, "event": event, "repositories": len(saved)}

    if event == "pull_request" and action in PR_ACTIONS:
        pull_request = await sync_pull_request(db, payload)
        if pull_request is None:
            return {"ok": True, "event": event, "synced": False}
        return {"ok": True, "event": event, "synced": True, "pr_number": pull_request.number}

    return {"ok": True, "event": event}
