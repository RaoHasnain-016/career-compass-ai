import re
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models import Career, Recommendation, SavedCareer, StudentProfile, StudentUpdate, StudentUpdateRead


INBOX_LIMIT = 40

# Give each public release notice a permanent ID so it stays read across releases.
PLATFORM_NOTICES = (
    {
        "id": "platform:notifications-and-study-options-v1",
        "title": "Your notification inbox and study options are ready",
        "summary": "Check your inbox for profile updates and career news. Open Study Options for the next step in your education.",
        "category": "platform",
        "url": "/universities",
        "source": "Career Compass AI",
        "published_at": "2026-11-26T00:00:00+05:00",
    },
    {
        "id": "platform:education-pathways-2026-11",
        "title": "Education pathways and individual skill gaps",
        "summary": "Profile setup now tailors interests and skills to your field. Select a career in Skill Gap to see its own learning priorities.",
        "category": "platform",
        "url": "/profile-setup",
        "source": "Career Compass AI",
        "published_at": "2026-11-26T00:00:00+05:00",
    },
)

FIELD_ALIASES = {
    "technology": ("technology", "computing", "computer science", "software", "cybersecurity", "ics", "advanced technical role", "it support"),
    "data": ("data", "analytics", "statistics", "artificial intelligence"),
    "engineering": ("engineering", "electrical", "mechanical", "civil technology", "electronics", "construction"),
    "health": ("health", "medical", "pharmacy", "nursing", "biology"),
    "business": ("business", "management", "commerce", "finance", "accounting", "icom", "marketing"),
    "design": ("design", "creative arts", "visual art"),
    "education": ("teaching", "education", "academia"),
    "law": ("law", "legal"),
    "architecture": ("architecture", "built environment"),
    "media": ("media", "journalism", "communications"),
    "social_sciences": ("social sciences", "social impact", "humanities", "psychology", "sociology"),
    "science": ("science", "research", "chemistry", "physics", "mathematics", "environment"),
}

COUNTRY_ALIASES = {
    "uk": "united kingdom", "england": "united kingdom", "great britain": "united kingdom",
    "usa": "united states", "us": "united states", "united states of america": "united states",
}


@dataclass(frozen=True)
class UpdateAudience:
    stage: str = "exploring"
    country: str = ""
    fields: tuple[str, ...] = ()


def education_stage(level):
    level = str(level or "").casefold()
    if re.search(r"\b(diploma|dae|technical|vocational|vet|polytechnic|associate degree|short.cycle|post.secondary)\b", level):
        return "diploma"
    if re.search(r"\b(intermediate|senior secondary|upper secondary|sixth form|a.level|high school senior|class (11|12)|hssc)\b", level):
        return "senior_secondary"
    if re.search(r"\b(matric|secondary|gcse|class 9|class 10|middle|high school|ssc)\b", level):
        return "school"
    if re.search(r"\b(bachelor\w*|undergraduate)\b", level):
        return "undergraduate"
    if re.search(r"\b(master\w*|graduate|postgraduate|doctoral|phd)\b", level):
        return "postgraduate"
    return "exploring"


def academic_fields(value):
    value = str(value or "").casefold().replace("_", " ")
    # When a specific computing or health label mentions 'science', prefer its discipline.
    fields = [field for field, aliases in FIELD_ALIASES.items() if any(
        re.search(rf"\b{re.escape(alias)}\b", value) for alias in aliases
    )]
    if len(fields) > 1 and "science" in fields and "science" not in value.split(" & "):
        fields.remove("science")
    if "engineering" in fields and value in {"civil technology", "electrical technology", "mechanical technology", "electronics technology"}:
        fields.remove("technology")
    if value == "architecture technology":
        return ["architecture"]
    return fields


def _preferences(value):
    parts = str(value or "").split("|")
    return {key.strip().casefold(): content.strip() for part in parts
            for key, delimiter, content in [part.partition(":")] if delimiter}


def load_audience(db, user_id):
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if not profile:
        return UpdateAudience()

    preferences = _preferences(profile.study_preference)
    fields = []
    if profile.selected_career_id:
        selection = db.scalar(select(Career.field).where(
            Career.career_id == profile.selected_career_id, Career.status.is_(True)
        ))
        fields.extend(academic_fields(selection))
    fields.extend(academic_fields(preferences.get("career direction")))
    if not fields:
        fields.extend(academic_fields(preferences.get("education stream")))
    saved = db.scalars(select(Career.field).join(SavedCareer).where(
        SavedCareer.user_id == user_id, Career.status.is_(True),
    ).order_by(SavedCareer.created_at.desc(), Career.title).limit(3))
    for field in saved:
        fields.extend(academic_fields(field))
    matches = db.scalars(select(Career.field).join(Recommendation).where(
        Recommendation.user_id == user_id,
        Recommendation.confidence_level.in_(("Very Strong Match", "Strong Match", "Moderate Match")),
        Career.status.is_(True),
    ).order_by(Recommendation.match_score.desc(), Career.title).limit(3))
    for match in matches:
        fields.extend(academic_fields(match))

    return UpdateAudience(
        stage=education_stage(profile.academic_level),
        country=profile.country or preferences.get("country", ""),
        fields=tuple(dict.fromkeys(fields))[:3],
    )


def _country(value):
    value = str(value or "").strip().casefold()
    return COUNTRY_ALIASES.get(value, value)


def news_matches(item, audience):
    if audience.stage == "exploring":
        return False
    fields, stages = set(item.get("fields") or []), set(item.get("stages") or [])
    if stages and audience.stage not in stages:
        return False
    if fields and not fields.intersection(audience.fields):
        return False
    if not fields and not stages:
        return False
    source_country = _country(item.get("country"))
    # Programme/qualification news only applies to the relevant education system.
    if source_country and source_country != _country(audience.country):
        return bool(not stages and item.get("source", "").startswith("O*NET"))
    return True


def news_category(article):
    if article.get("stages") and re.search(r"\b(admissions?|scholarships?|applications?|aptitude test)\b", article["title"], re.IGNORECASE):
        return "admissions"
    return "career_news"


def _published(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not value.tzinfo:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def record_student_update(db, user_id, *, category, title, summary, url):
    db.add(StudentUpdate(user_id=user_id, category=category, title=title, summary=summary, url=url))


def inbox_items(db, user_id, audience, news_items):
    events = db.scalars(select(StudentUpdate).where(StudentUpdate.user_id == user_id)
                        .order_by(StudentUpdate.published_at.desc(), StudentUpdate.update_id.desc())
                        .limit(INBOX_LIMIT))
    items = [dict(item) for item in PLATFORM_NOTICES]
    items.extend({
        "id": f"student:{event.update_id}", "category": event.category, "title": event.title,
        "summary": event.summary, "url": event.url, "source": "Career Compass AI",
        "published_at": _published(event.published_at).isoformat(),
    } for event in events)
    items.extend({
        **{key: article[key] for key in ("title", "summary", "url", "source", "published_at")},
        "id": f"news:{article['id']}", "category": news_category(article),
        "country": article.get("country"),
    } for article in news_items if news_matches(article, audience))

    # Providers use canonical URLs as the basis for stable article IDs.
    unique = {}
    for item in sorted(items, key=lambda row: (_published(row["published_at"]), row["id"]), reverse=True):
        unique.setdefault(item["id"], item)
    visible = list(unique.values())[:INBOX_LIMIT]
    if not visible:
        return []
    read_ids = set(db.scalars(select(StudentUpdateRead.notification_id).where(
        StudentUpdateRead.user_id == user_id,
        StudentUpdateRead.notification_id.in_([row["id"] for row in visible]),
    )))
    return [{**row, "read": row["id"] in read_ids} for row in visible]


def mark_visible_read(db, user_id, visible, requested):
    ids = {item["id"] for item in visible} & set(requested)
    unread_ids = {item["id"] for item in visible if not item["read"]}
    new_reads = ids & unread_ids
    if new_reads:
        insert = sqlite_insert if db.bind.dialect.name == "sqlite" else postgres_insert
        db.execute(insert(StudentUpdateRead).values([
            {"user_id": user_id, "notification_id": item_id} for item_id in sorted(new_reads)
        ]).on_conflict_do_nothing(index_elements=["user_id", "notification_id"]))
        db.commit()
    return {"read_ids": sorted(ids), "unread_count": len(unread_ids - ids)}
