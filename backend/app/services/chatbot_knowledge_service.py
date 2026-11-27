"""Retrieve dated official evidence for local chatbot questions."""

import re

from app.services.career_news_service import get_career_news
from app.services.local_chat_service import reply_language
from app.services.student_updates_service import news_category, news_matches
from app.services.university_suggestion_service import get_university_suggestions


_STUDY_QUESTION = re.compile(
    r"\b(admissions?|deadlines?|scholarships?|dakhla|dakhle|akhri tareekh)\b"
    r"|\b(?:can|could|should) i apply (?:today|tomorrow|this (?:week|month|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday))\b"
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


_EVIDENCE_REPLIES = {
    "en": {
        "school_pathway": "At your current school stage, compare senior-secondary or recognised technical options first. Ask your board or institution which subjects keep your intended degree pathway open.",
        "profile_needed": "Add your country and education stage in Profile Setup so I can look up relevant official notices.",
        "unverified": "I couldn't verify any current official notices for your profile. Check Study Options and confirm dates on the institution's website.",
        "no_match": "I didn't find a matching official source for your education stage and career area.",
        "study_options": "These official pages are starting points for your study stage and field. Confirm subject requirements and application dates with each institution.",
        "admissions": "These official notices match your profile. Open the original notice to confirm the current deadline, entry qualifications and whether you can apply.",
        "career_news": "Here are the official career updates I found for your profile. Check each publisher's date and geographic scope.",
    },
    "ur": {
        "school_pathway": "اپنی موجودہ جماعت کے بعد انٹرمیڈیٹ اور تسلیم شدہ فنی پروگراموں کا موازنہ کریں۔ اپنے بورڈ یا ادارے سے پوچھیں کہ آپ کی پسند کی ڈگری کے لیے کون سے مضامین ضروری ہیں۔",
        "profile_needed": "پروفائل سیٹ اپ میں اپنا ملک اور تعلیم کی سطح درج کریں تاکہ میں متعلقہ سرکاری اطلاعات تلاش کر سکوں۔",
        "unverified": "میں آپ کے لیے موجودہ سرکاری اطلاع کی تصدیق نہیں کر سکا۔ داخلے کی آخری تاریخ ادارے کے سرکاری صفحے سے معلوم کریں۔",
        "no_match": "آپ کی تعلیم کی سطح اور شعبے کے مطابق کوئی متعلقہ سرکاری اطلاع نہیں ملی۔",
        "study_options": "یہ سرکاری صفحات آپ کے شعبے میں پڑھائی کے اختیارات سمجھنے میں مدد دیں گے۔ مطلوبہ مضامین اور درخواست کی تاریخ متعلقہ ادارے سے معلوم کریں۔",
        "admissions": "یہ سرکاری اطلاعات آپ کی پروفائل سے متعلق ہیں۔ آخری تاریخ اور داخلے کی اہلیت کے لیے اصل اطلاع دیکھیں۔",
        "career_news": "یہ سرکاری اطلاعات آپ کے کیریئر سے متعلق ہیں۔ ہر خبر کی تاریخ اور یہ کس ملک یا علاقے کے لیے ہے، اصل صفحے پر دیکھیں۔",
    },
    "ur-Latn": {
        "school_pathway": "Apni maujooda class ke baad Intermediate aur tasleem shuda technical programs ka muqabla karein. Apne board ya idare se poochhein ke pasand ki degree ke liye kaun se subjects zaroori hain.",
        "profile_needed": "Profile Setup mein apna mulk aur taleem ki satah darj karein, taake main aap se mutalliq official updates dhoondh sakun.",
        "unverified": "Mujhe aap ke liye kisi taza official notice ki tasdeeq nahi mili. Dakhle ki aakhri tareekh idare ke official page par check karein.",
        "no_match": "Aap ki taleem ki satah aur field ke mutabiq koi official notice nahi mila.",
        "study_options": "In official pages se apni field ke study options dekhein. Zaroori subjects aur apply karne ki tareekh idare se confirm karein.",
        "admissions": "Ye official notices aap ki profile se mutalliq hain. Aakhri tareekh aur dakhle ki eligibility asal notice par check karein.",
        "career_news": "Ye official updates aap ke career se mutalliq hain. Asal page par tareekh aur mulk ya ilaqa check karein.",
    },
}


def evidence_only_answer(evidence, question=""):
    """Use the same evidence requirements in each supported reply language."""
    status = evidence["status"]
    if status in {"school_pathway", "profile_needed"}:
        key = status
    elif not evidence["items"]:
        key = "unverified" if status in {"unavailable", "stale", "offline"} else "no_match"
    else:
        key = evidence["topic"]
    return _EVIDENCE_REPLIES[reply_language(question)][key]
