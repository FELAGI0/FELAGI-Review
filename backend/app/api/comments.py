from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Comment, PullRequest
from app.security import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pr_id: UUID
    user_id: UUID
    parent_id: UUID | None = None
    file_path: str | None = None
    line_number: int | None = None
    body: str
    resolved: bool
    created_at: datetime
    updated_at: datetime
    author_username: str | None = None


class CommentCreate(BaseModel):
    file_path: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    body: str = Field(min_length=1, max_length=10_000)
    parent_id: UUID | None = None


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class CommentThread(BaseModel):
    root: CommentOut
    replies: list[CommentOut]


async def _get_pr_or_404(db: AsyncSession, pr_id: UUID) -> PullRequest:
    result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return pr


async def _get_comment_or_404(db: AsyncSession, comment_id: UUID) -> Comment:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def _with_author(comment: Comment, usernames: dict[UUID, str]) -> CommentOut:
    out = CommentOut.model_validate(comment)
    out.author_username = usernames.get(comment.user_id)
    return out


@router.get("/prs/{pr_id}/comments")
async def list_comments(
    pr_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CommentThread]:
    await _get_pr_or_404(db, pr_id)
    result = await db.execute(
        select(Comment)
        .where(Comment.pr_id == pr_id)
        .order_by(Comment.created_at)
    )
    comments = list(result.scalars())
    if not comments:
        return []

    from app.models import User

    user_ids = {c.user_id for c in comments}
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    usernames = {u.id: u.username for u in users_result.scalars()}

    roots: dict[UUID, CommentThread] = {}
    replies_by_parent: dict[UUID, list[CommentOut]] = {}

    for comment in comments:
        out = _with_author(comment, usernames)
        if comment.parent_id is None:
            roots[comment.id] = CommentThread(root=out, replies=[])
        else:
            replies_by_parent.setdefault(comment.parent_id, []).append(out)

    threads: list[CommentThread] = []
    for comment_id, thread in roots.items():
        thread.replies = _collect_replies(comment_id, replies_by_parent)
        threads.append(thread)
    for orphan_id in list(replies_by_parent):
        for orphan in replies_by_parent.pop(orphan_id):
            threads.append(CommentThread(root=orphan, replies=[]))

    return threads


def _collect_replies(
    parent_id: UUID, replies_by_parent: dict[UUID, list[CommentOut]]
) -> list[CommentOut]:
    collected: list[CommentOut] = []
    for reply in replies_by_parent.pop(parent_id, []):
        collected.append(reply)
        collected.extend(_collect_replies(reply.id, replies_by_parent))
    return collected


@router.post("/prs/{pr_id}/comments", status_code=201)
async def create_comment(
    pr_id: UUID,
    payload: CommentCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentOut:
    await _get_pr_or_404(db, pr_id)

    if payload.parent_id is not None:
        parent = await _get_comment_or_404(db, payload.parent_id)
        if parent.pr_id != pr_id:
            raise HTTPException(
                status_code=400, detail="Parent comment belongs to another PR"
            )
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=400, detail="Nested replies are not allowed"
            )

    comment = Comment(
        id=uuid4(),
        pr_id=pr_id,
        user_id=UUID(user["id"]),
        parent_id=payload.parent_id,
        file_path=payload.file_path,
        line_number=payload.line_number,
        body=payload.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


@router.patch("/comments/{comment_id}")
async def update_comment(
    comment_id: UUID,
    payload: CommentUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentOut:
    comment = await _get_comment_or_404(db, comment_id)
    if comment.user_id != UUID(user["id"]):
        raise HTTPException(status_code=403, detail="Not the comment author")
    comment.body = payload.body
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    comment = await _get_comment_or_404(db, comment_id)
    if comment.user_id != UUID(user["id"]):
        raise HTTPException(status_code=403, detail="Not the comment author")
    result = await db.execute(
        select(Comment).where(Comment.parent_id == comment_id)
    )
    replies = list(result.scalars())
    if replies:
        for reply in replies:
            reply.parent_id = None
    await db.delete(comment)
    await db.commit()


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    comment = await _get_comment_or_404(db, comment_id)
    comment.resolved = not comment.resolved
    await db.commit()
    return {"id": str(comment.id), "resolved": comment.resolved}
