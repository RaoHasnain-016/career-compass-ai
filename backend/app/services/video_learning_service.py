from collections import defaultdict
import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from app.models.video_resource_model import VideoResource
from app.services.resource_service import normalize_text
from app.services.youtube_service import search_youtube_videos, youtube_video_links


logger = logging.getLogger(__name__)

# Publisher-linked starter lessons. Each lesson covers only its listed skills.
_STARTER_LESSONS = (
    (("communication", "presentation", "public speaking"), "HAnw168huqA",
     "Think Fast, Talk Smart: Communication Techniques", "Stanford Graduate School of Business"),
    (("programming", "python"), "rfscVS0vtbw", "Learn Python for Beginners", "freeCodeCamp.org"),
    (("database", "databases", "sql"), "HXV3zeQKqGY", "SQL and Databases for Beginners", "freeCodeCamp.org"),
    (("web development", "html", "css"), "a_iQb1lnAEQ", "Learn HTML and CSS for Beginners", "freeCodeCamp.org"),
    (("git", "github", "version control"), "RGOj5yH7evk", "Git and GitHub for Beginners", "freeCodeCamp.org"),
    (("excel", "spreadsheets", "computer applications"), "Vl0H-qTclOg",
     "Microsoft Excel Tutorial for Beginners", "freeCodeCamp.org"),
    (("design", "ui design", "figma"), "zzhSFobLkYw", "Figma Design for Beginners: Course Overview", "Figma"),
)


def _stored_videos(db, *filters):
    try:
        return db.query(VideoResource).filter(*filters).all()
    except (OperationalError, ProgrammingError) as error:
        # Older installations may lack the optional video cache table.
        original = error.orig
        missing_cache = (
            getattr(original, "pgcode", None) == "42P01"
            or "no such table: video_resources" in str(original).lower()
        )
        if not missing_cache:
            raise
        db.rollback()
        logger.info("Video cache table unavailable; serving lessons without persistence")
        return None


def _video_payload(video, skill):
    links = youtube_video_links(video.youtube_video_id)
    if not links or not video.status or not video.is_free:
        return None
    return {
        **links,
        "video_resource_id": str(video.video_resource_id),
        "title": video.title,
        "channel_title": video.channel_title,
        "skill": skill,
        "career_field": video.career_field,
        "difficulty": video.difficulty,
        "source": video.source,
        "source_type": "saved",
        "is_free": True,
        "status": True,
    }


def _live_videos(db, query, skill, career_field, cache_available):
    items = search_youtube_videos(query, max_results=3)
    if not items:
        return []

    existing = _stored_videos(
        db, VideoResource.youtube_video_id.in_([item["youtube_video_id"] for item in items]),
    ) if cache_available else None
    by_id = {video.youtube_video_id: video for video in existing or []}
    seen = set()
    pending = []
    results = []
    for item in items:
        video_id = item["youtube_video_id"]
        if video_id in seen:
            continue
        seen.add(video_id)
        saved = by_id.get(video_id)
        if saved and (not saved.status or not saved.is_free):
            continue
        video = {
            **item, "skill": skill, "career_field": career_field,
            "source": "YouTube", "difficulty": "Beginner", "is_free": True, "status": True,
        }
        if existing is not None and saved is None:
            pending.append(VideoResource(**video))
        results.append({**video, "source_type": "youtube"})
    if pending:
        db.add_all(pending)
        try:
            db.commit()
        except IntegrityError:
            # A concurrent request may have saved the same globally unique video.
            db.rollback()
    return results


def recommend_video_courses(db, career_title, career_field, required_skills, missing_skills, *, live):
    topics = list(dict.fromkeys(
        skill for value in [*missing_skills, *required_skills] if (skill := normalize_text(value))
    ))[:5]
    if not topics:
        return []

    stored = _stored_videos(db, func.lower(func.trim(VideoResource.skill)).in_(topics))
    by_skill = defaultdict(list)
    excluded_ids = {video.youtube_video_id for video in stored or [] if not video.status or not video.is_free}
    for video in sorted(
        stored or [],
        key=lambda item: (normalize_text(item.career_field) != normalize_text(career_field), item.title.casefold()),
    ):
        skill = normalize_text(video.skill)
        if payload := _video_payload(video, skill):
            by_skill[skill].append(payload)

    for matching_skills, video_id, title, channel in _STARTER_LESSONS:
        skill = next((topic for topic in topics if topic in matching_skills), None)
        if skill and video_id not in excluded_ids:
            by_skill[skill].append({
                **youtube_video_links(video_id),
                "title": title, "channel_title": channel, "skill": skill, "career_field": career_field,
                "difficulty": "Beginner", "source": "YouTube", "source_type": "starter",
                "is_free": True, "status": True,
            })

    uncovered = next((topic for topic in topics if not by_skill[topic]), None)
    if live and uncovered:
        # Copy the relevant fields above and return the read connection before network I/O.
        db.rollback()
        query = f"{uncovered} beginner tutorial {career_title}"
        by_skill[uncovered] = _live_videos(db, query, uncovered, career_field, stored is not None)

    unique = {}
    for topic in topics:
        for video in by_skill[topic][:3]:
            unique.setdefault(video["youtube_video_id"], video)
    return list(unique.values())
