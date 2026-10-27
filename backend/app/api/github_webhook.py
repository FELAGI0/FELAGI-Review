from typing import Any

from fastapi import APIRouter, Request

from app.logging import logger
from app.services.github_app import GitHubAppClient, WebhookSignatureError

router = APIRouter()

PR_ACTIONS = {"opened", "synchronize", "reopened"}


@router.post("/webhooks/github", status_code=200)
async def github_webhook(request: Request) -> dict[str, Any]:
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

    if event == "pull_request" and action in PR_ACTIONS:
        pr = payload.get("pull_request") or {}
        repository = payload.get("repository") or {}
        installation = payload.get("installation") or {}
        logger.info(
            "pr_event",
            repo=repository.get("full_name"),
            number=pr.get("number"),
            state=pr.get("state"),
            title=pr.get("title"),
            installation_id=installation.get("id"),
        )

    if event == "installation" and action == "created":
        installation = payload.get("installation") or {}
        logger.info(
            "installation_created",
            installation_id=installation.get("id"),
            account=(installation.get("account") or {}).get("login"),
        )

    return {"ok": True, "event": event}
