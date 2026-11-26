import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.database import SessionLocal
from app.models import User
from app.services.career_news_service import get_career_news
from app.services.student_updates_service import (
    INBOX_LIMIT, inbox_items, load_audience, mark_visible_read, news_category, news_matches,
)
from app.services.university_suggestion_service import get_university_suggestions
from app.utils.auth_dependency import get_current_firebase_user


router = APIRouter(prefix="/student-updates", tags=["Student Updates"])

NotificationId = Annotated[str, StringConstraints(min_length=1, max_length=120)]


class ReadNotifications(BaseModel):
    ids: list[NotificationId] = Field(min_length=1, max_length=INBOX_LIMIT)


def current_student_id(firebase_user=Depends(get_current_firebase_user)) -> UUID:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.firebase_uid == firebase_user.get("uid")))
        if not user:
            raise HTTPException(404, "Student account not found. Please sign in again.")
        if str(user.role).casefold() != "student" or str(user.status or "active").casefold() != "active":
            raise HTTPException(403, "Student updates are for active student accounts.")
        return user.user_id


def get_audience(user_id):
    with SessionLocal() as db:
        return load_audience(db, user_id)


def get_inbox(user_id, audience, articles, read_ids=None):
    with SessionLocal() as db:
        items = inbox_items(db, user_id, audience, articles)
        if read_ids is not None:
            return mark_visible_read(db, user_id, items, read_ids)
        return items


async def fetch_updates(user_id):
    audience = await run_in_threadpool(get_audience, user_id)
    return audience, await feed_for_audience(audience)


async def feed_for_audience(audience):
    if audience.stage == "exploring" or not (audience.fields or audience.country):
        return {"items": [], "checked_at": None, "status": "profile_needed", "sources": []}
    return await get_career_news()


@router.get("/notifications")
async def notifications(response: Response, user_id: UUID = Depends(current_student_id)):
    response.headers["Cache-Control"] = "private, no-store"
    audience, feed = await fetch_updates(user_id)
    items = await run_in_threadpool(get_inbox, user_id, audience, feed["items"])
    return {
        "items": items,
        "unread_count": sum(not item["read"] for item in items),
        "refreshed_at": feed["checked_at"],
        "feed_status": feed["status"],
        "feed_sources": feed.get("sources", []),
        "stage": audience.stage,
    }


@router.post("/notifications/read")
async def read_notifications(
    body: ReadNotifications, response: Response, user_id: UUID = Depends(current_student_id),
):
    response.headers["Cache-Control"] = "private, no-store"
    audience, feed = await fetch_updates(user_id)
    return await run_in_threadpool(get_inbox, user_id, audience, feed["items"], body.ids)


@router.get("/universities")
async def universities(response: Response, user_id: UUID = Depends(current_student_id)):
    response.headers["Cache-Control"] = "private, no-store"
    audience = await run_in_threadpool(get_audience, user_id)
    field = audience.fields[0] if audience.fields else ""
    suggestions, feed = await asyncio.gather(
        get_university_suggestions(country=audience.country, field=field, stage=audience.stage),
        feed_for_audience(audience),
    )
    admissions = [
        {key: item.get(key) for key in ("id", "title", "summary", "source", "url", "published_at", "expires_at")}
        for item in feed["items"]
        if news_matches(item, audience) and news_category(item) == "admissions"
    ][:5]
    return {
        **suggestions, "profile_country": audience.country, "profile_field": field,
        "admissions_updates": admissions, "admissions_status": feed["status"],
    }
