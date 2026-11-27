"""Retrieve dated official evidence for local chatbot questions."""

import re

from app.services.career_news_service import get_career_news
from app.services.student_updates_service import news_category, news_matches
from app.services.university_suggestion_service import get_university_suggestions


_STUDY_QUESTION = re.compile(
    r"\b(admissions?|deadlines?|scholarships?|dakhla|dakhle|akhri tareekh)\b"
    r"|داخل[ہے]|وظیف[ہے]|آخری تاریخ", re.IGNORECASE,
)
_UNIVERSITY_QUESTION = re.compile(r"\b(universit\w*|colleges?|study abroad)\b|یونیورسٹ", re.IGNORECASE)
_NEWS_QUESTION = re.compile(
    r"\b(news|latest|current updates?|recent updates?|kia naya|nayi khabar|taza)\b|تازہ|خبریں", re.IGNORECASE,
)


def knowledge_topic(question):
    if _STUDY_QUESTION.search(question):
        return "admissions"
    if _UNIVERSITY_QUESTION.search(question):
        return "study_options"
    if _NEWS_QUESTION.search(question):
        return "career_news"
    return None


def empty_evidence(topic, stage, status):
    return {"topic": topic, "stage": stage, "status": status, "checked_at": None, "items": []}


async def retrieve_chat_evidence(topic, audience):
    if audience.stage == "exploring":
        return empty_evidence(topic, audience.stage, "profile_needed")
    if topic == "study_options" or (topic == "admissions" and audience.stage == "school"):
        study = await get_university_suggestions(
            country=audience.country, field=next(iter(audience.fields), ""), stage=audience.stage,
        )
        guides = [
            {"title": source["title"], "source": source["institution"], "url": source["url"],
             "note": source["note"], "checked_at": source["checked_at"], "country": source["country"]}
            for source in [*study["domestic"][:2], *study["international"][:2], *study["sources"]]
            if source["verification_status"] in {"verified", "cached"}
        ]
        return {
            "topic": topic, "stage": audience.stage,
            "status": "school_pathway" if audience.stage == "school" else "official_guide",
            "checked_at": study["checked_at"],
            "items": list({source["url"]: source for source in guides}.values())[:4],
        }

    feed = await get_career_news()
    sources = []
    for item in feed["items"]:
        if news_category(item) != topic or not news_matches(item, audience):
            continue
        sources.append({
            **{key: item[key] for key in ("title", "summary", "url", "source", "published_at")},
            "country": item.get("country"),
            "note": "Check the official notice for the application window and exact eligibility."
            if topic == "admissions" else "Check the original publisher for the geographic scope.",
        })
        if len(sources) == 3:
            break
    return {
        "topic": topic, "stage": audience.stage, "status": feed["status"],
        "checked_at": feed["checked_at"], "items": sources,
    }


def evidence_only_answer(evidence):
    """For time-sensitive topics, use only a claim the source actually supports."""
    if evidence["status"] == "school_pathway":
        return (
            "At your current school stage, compare senior-secondary or recognised technical options first. "
            "Ask your board or institution which subjects keep your intended degree pathway open."
        )
    if evidence["status"] == "profile_needed":
        return "Add your country and education stage in Profile Setup so I can look up relevant official notices."
    if not evidence["items"]:
        if evidence["status"] in {"unavailable", "stale", "offline"}:
            return "I couldn't verify any current official notices for your profile. Check Study Options and confirm dates on the institution's website."
        return "I didn't find a matching official source for your education stage and career area."
    if evidence["topic"] == "study_options":
        return "These official pages are starting points for your study stage and field. Confirm subject requirements and application dates with each institution."
    if evidence["topic"] == "admissions":
        return (
            "These official notices match your profile. Open the original notice to confirm the current deadline, "
            "entry qualifications and whether you can apply."
        )
    return "Here are the official career updates I found for your profile. Check each publisher's date and geographic scope."
