"""Answer profile-specific questions from the student's saved career evidence."""

import json
import re

from app.services.education_stage_service import education_stage
from app.services.local_chat_service import reply_language
from app.services.resource_service import find_missing_skills


_COMPARE = re.compile(r"\b(?:compar\w*|difference between|versus|vs|muqabla|farq)\b|موازنہ|مقابلہ|فرق", re.I)
_CAREER_CONTEXT = re.compile(r"\b(?:career\w*|path\w*|option\w*|recommendation\w*|degree\w*|program\w*|top two)\b|کیریئر|ڈگری|شعب", re.I)
_TOP_OPTIONS = re.compile(r"\b(?:top|my recommendations|my careers|first|second|pehle|doosre)\b|پہلے دو|اپنے دو", re.I)
_WHY = re.compile(
    r"\b(?:why|how|ky[uo]n)\b.{0,85}\b(?:recommend\w*|career match|career fit|fit my profile)\b"
    r"|\bcareer\b.{0,35}\bky[uo]n\b|کیریئر.{0,40}کیوں|کیوں.{0,40}(?:سفارش|کیریئر)", re.I,
)
_SKILLS = re.compile(
    r"\b(?:skill gaps?|missing skills?|skills? (?:should i|do i need to) (?:improve|learn)"
    r"|(?:which|what|konsi|kaunsi) skills?\b.{0,40}\b(?:first|pehle|seekh\w*))\b|(?:کون سی مہارت|مہارتوں کی کمی)", re.I,
)
_PATH = re.compile(
    r"\b(?:what career (?:would |does )?suit\w* me|what career should i (?:choose|explore)"
    r"|which career\b.{0,35}\b(?:profile|for me|choose)|(?:career|study) options (?:are there )?for my (?:program\w*|degree|diploma|profile)"
    r"|what (?:can|should) i (?:study|do next|do) after (?:my )?(?:matric|intermediate|diploma|degree))\b"
    r"|\b(?:mera|meri|mere)\b.{0,50}\b(?:career|degree|diploma)\b.{0,40}\b(?:behtar|kons[ai]|kauns[ai])\b"
    r"|میرے لیے کون سا شعبہ|میرے لیے کون سا کیریئر", re.I,
)
_FOLLOW_UP = re.compile(r"(?:and\s+)?why\s+(?:the\s+)?(first|second)(?:\s+one)?[.?!]*", re.I)
_SOURCE_QUESTION = re.compile(
    r"\b(?:admissions?|deadlines?|scholarships?|dakhla|dakhle|akhri tareekh|eligible to apply)\b"
    r"|داخل[ہے]|وظیف[ہے]|آخری تاریخ", re.I,
)
_ROMAN_INTENT = re.compile(r"\b(?:ky[uo]n|pehle|doosre|muqabla|behtar|kauns[ai]|kons[ai])\b", re.I)


_COPY = {
    "en": {
        "need_profile": "What are you studying now, and which career or subject would you like to explore?",
        "need_two": "Which two careers or programs should I compare? I can see {count} in your saved matches.",
        "need_choice": "Which career do you mean? Tell me its name so I can explain its match.",
        "options": "Here are the top matches from your saved profile.",
        "program": "Your saved program is {program}. Here are the top matches from your profile.",
        "compare": "Here's how those paths compare in your saved profile.",
        "match": "{title} has a profile match of {score}%.",
        "record": "Your saved match for {title} is based on these profile details.",
        "no_match": "I don't have a scored match for {title}. Which subjects or skills are you hoping to use in that path?",
        "matched": "Your matched skills include {items}.",
        "subjects": "Matching subjects include {items}.",
        "gaps": "Recorded skill gaps include {items}.",
        "missing_details": "The saved match has no specific skill or subject details to compare.",
        "compare_next": "Which matters more to you right now, the subjects you enjoy or the skills you would need to build?",
        "school_next": "At your school stage, compare subject groups and technical pathways to see which keep this option open.",
        "foundation": "Use this match to explore a pathway and plan its academic requirements.",
        "check_requirements": "Your saved assessment identifies academic requirements to work on before pursuing this path.",
        "first_skill": "For {title}, {skill} is a good starting point from your saved skill gaps.",
        "roadmap_skill": "It appears in your next recorded roadmap step.",
        "resource_skill": "A matching learning resource is available in your saved guidance.",
        "no_gaps": "I don't see a recorded skill gap for {title}. Which skill or roadmap step would you like to practice?",
        "priority_unknown": "The profile didn't rank the gaps, so treat this as a starting point.",
    },
    "ur-Latn": {
        "need_profile": "Aap abhi kya parh rahe hain aur kis career ya subject ko explore karna chahte hain?",
        "need_two": "Kin do careers ya programs ka muqabla karun? Aap ki profile mein abhi {count} saved matches hain.",
        "need_choice": "Aap kis career ki baat kar rahe hain? Naam batayein taake main match samjha sakun.",
        "options": "Aap ki saved profile ke mutabiq ye aap ke top career matches hain.",
        "program": "Aap ka darj shuda program {program} hai. Ye aap ki profile ke top matches hain.",
        "compare": "Aap ki saved profile mein in raaston ka muqabla yeh hai.",
        "match": "{title} aap ki profile se {score}% match karta hai.",
        "record": "{title} ka saved match in profile details par mabni hai.",
        "no_match": "{title} ka score meri maloomat mein nahi hai. Is raaste mein aap kaun se subjects ya skills use karna chahte hain?",
        "matched": "Aap ki matching skills mein {items} shamil hain.",
        "subjects": "Matching subjects mein {items} shamil hain.",
        "gaps": "Recorded skill gaps mein {items} shamil hain.",
        "missing_details": "Saved match mein muqable ke liye specific skills ya subjects darj nahi hain.",
        "compare_next": "Aap ke liye abhi kya zyada zaroori hai, pasand ke subjects ya woh skills jo aap seekhna chahte hain?",
        "school_next": "School ki is satah par subject groups aur technical pathways ka muqabla karein jo is raaste ko khula rakhein.",
        "foundation": "Is match se raasta samjhein aur us ki taleemi sharaait ke liye plan banayein.",
        "check_requirements": "Saved assessment mein is raaste ke liye kuch taleemi sharaait par kaam karna baqi hai.",
        "first_skill": "{title} ke liye saved skill gaps mein se {skill} se shuru kar sakte hain.",
        "roadmap_skill": "Yeh skill aap ke roadmap ke agle darj shuda qadam mein hai.",
        "resource_skill": "Aap ki saved guidance mein is skill ka learning resource hai.",
        "no_gaps": "{title} ke liye koi skill gap darj nahi hai. Aap kis skill ya roadmap step ki practice karna chahte hain?",
        "priority_unknown": "Profile mein gaps ki tarteeb darj nahi hai, is liye ise ek pehla qadam samjhein.",
    },
    "ur": {
        "need_profile": "آپ ابھی کیا پڑھ رہے ہیں، اور کس کیریئر یا مضمون کے بارے میں جاننا چاہتے ہیں؟",
        "need_two": "کن دو شعبوں یا پروگراموں کا موازنہ کریں؟ آپ کی پروفائل میں ابھی {count} محفوظ مماثلتیں ہیں۔",
        "need_choice": "آپ کا مطلب کون سا کیریئر ہے؟ نام بتائیں تاکہ میں اس کی مماثلت سمجھا سکوں۔",
        "options": "آپ کی محفوظ پروفائل کے مطابق ان شعبوں سے آپ کی سب سے زیادہ مماثلت ہے۔",
        "program": "آپ کا درج شدہ پروگرام {program} ہے۔ آپ کی پروفائل کے مطابق ان شعبوں سے سب سے زیادہ مماثلت ہے۔",
        "compare": "آپ کی محفوظ پروفائل کے مطابق ان راستوں کا موازنہ یہ ہے۔",
        "match": "{title} سے آپ کی پروفائل کی مماثلت {score} فیصد ہے۔",
        "record": "{title} کی محفوظ مماثلت پروفائل کی ان تفصیلات پر مبنی ہے۔",
        "no_match": "{title} کے لیے محفوظ اسکور دستیاب نہیں۔ آپ اس شعبے میں کن مضامین یا مہارتوں سے کام لینا چاہتے ہیں؟",
        "matched": "متعلقہ مہارتوں میں {items} شامل ہیں۔",
        "subjects": "متعلقہ مضامین میں {items} شامل ہیں۔",
        "gaps": "جن مہارتوں پر کام کرنا باقی ہے، ان میں {items} شامل ہیں۔",
        "missing_details": "محفوظ مماثلت میں مخصوص مہارتوں یا مضامین کی تفصیل درج نہیں ہے۔",
        "compare_next": "اس وقت آپ کے لیے کیا زیادہ اہم ہے، پسندیدہ مضامین یا وہ مہارتیں جو آپ سیکھنا چاہتے ہیں؟",
        "school_next": "اس تعلیمی مرحلے پر ان مضمون گروپوں اور فنی پروگراموں کا موازنہ کریں جو اس شعبے کا راستہ کھلا رکھیں۔",
        "foundation": "اس مماثلت سے تعلیمی راستہ سمجھیں اور اس کے تقاضوں کے لیے منصوبہ بنائیں۔",
        "check_requirements": "آپ کی محفوظ جانچ کے مطابق اس راستے کے لیے بعض تعلیمی تقاضوں پر کام کرنا باقی ہے۔",
        "first_skill": "{title} کے لیے محفوظ مہارتوں کی فہرست میں سے {skill} پر کام شروع کر سکتے ہیں۔",
        "roadmap_skill": "یہ مہارت آپ کے روڈمیپ کے اگلے درج شدہ مرحلے میں شامل ہے۔",
        "resource_skill": "آپ کی محفوظ رہنمائی میں اس مہارت کو سیکھنے کا ذریعہ موجود ہے۔",
        "no_gaps": "{title} کے لیے کوئی مہارت کی کمی درج نہیں۔ آپ کس مہارت یا روڈمیپ مرحلے کی مشق کرنا چاہتے ہیں؟",
        "priority_unknown": "پروفائل میں ان مہارتوں کی ترجیح درج نہیں ہے، اس لیے اسے ایک ابتدائی قدم سمجھیں۔",
    },
}


def _records(value):
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _words(value):
    return [item.strip() for item in value if isinstance(item, str) and item.strip()][:12] if isinstance(value, list) else []


def _title(row):
    title = row.get("title")
    return title.strip() if isinstance(title, str) else ""


def _mentioned(message, options):
    matches = []
    for row in options:
        title = _title(row).casefold()
        if title and (match := re.search(rf"(?<!\w){re.escape(title)}(?!\w)", message.casefold())):
            matches.append((match.start(), row))
    return [row for _, row in sorted(matches, key=lambda item: item[0])]


def _summary(row, copy):
    title = _title(row)
    score = row.get("match_score")
    valid_score = type(score) in {float, int} and 0 <= score <= 100
    opener = copy["match"].format(title=title, score=f"{score:g}") if valid_score else copy["record"].format(title=title)
    evidence = []
    for field, key in (("matched_skills", "matched"), ("matched_subjects", "subjects"), ("missing_skills", "gaps")):
        if values := _words(row.get(field)):
            evidence.append(copy[key].format(items=", ".join(values[:3])))
    if not evidence:
        explanation = row.get("explanation")
        if copy is _COPY["en"] and isinstance(explanation, str) and explanation.strip() and not explanation.rstrip().endswith("..."):
            evidence.append(explanation.strip())
        else:
            evidence.append(copy["missing_details"])
    return " ".join([opener, *evidence])


def _stage_advice(profile, row, copy):
    if education_stage(profile.get("academic_level")) == "school":
        return copy["school_next"]
    return {
        "foundation_stage": copy["foundation"],
        "near_eligible": copy["check_requirements"],
        "below_requirement": copy["check_requirements"],
    }.get(row.get("eligibility_status"), "")


def _skill_answer(data, target, selected, copy):
    title = _title(target)
    gaps = _words(target.get("missing_skills"))
    if not gaps and _title(selected) == title and target.get("missing_skills") is None:
        known = _words(data["profile"].get("skills"))
        needed = _words(selected.get("required_skills"))
        missing = find_missing_skills(known, needed)
        gaps = [skill for skill in needed if skill.casefold() in missing]
    if not gaps:
        return copy["no_gaps"].format(title=title)

    evidence = ()
    if _title(selected) == title:
        stages = _records(data.get("roadmap"))
        next_skills = _words(stages[0].get("required_skills")) if stages else []
        resources = _records(data.get("learning_resources")) + _records(data.get("video_courses"))
        resource_skills = [row["skill"] for row in resources if isinstance(row.get("skill"), str)]
        evidence = ((next_skills, "roadmap_skill"), (resource_skills, "resource_skill"))
    for skills, reason in evidence:
        normalized = {skill.strip().casefold() for skill in skills}
        if first := next((skill for skill in gaps if skill.casefold() in normalized), None):
            return f"{copy['first_skill'].format(title=title, skill=first)} {copy[reason]}"
    return f"{copy['first_skill'].format(title=title, skill=gaps[0])} {copy['priority_unknown']}"


def answer_profile_analysis(message: str, context: str) -> str | None:
    """Use only the scoped context and leave unsupported questions to other routes."""
    question = message.strip()
    if _SOURCE_QUESTION.search(question):
        return None
    follow_up = _FOLLOW_UP.fullmatch(question)
    compare, explain, skills, pathway = (pattern.search(question) for pattern in (_COMPARE, _WHY, _SKILLS, _PATH))
    if not any((follow_up, compare, explain, skills, pathway)):
        return None
    try:
        data = json.loads(context) if len(context) <= 40_000 else {}
    except (ValueError, TypeError, RecursionError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    selected = data.get("selected_career")
    selected = selected if isinstance(selected, dict) else {}
    options = [row for row in _records(data.get("recommendations")) if _title(row)][:3]
    catalog = options + [selected] if _title(selected) and all(_title(row) != _title(selected) for row in options) else options
    named = _mentioned(question, catalog)
    if compare and not (named or _CAREER_CONTEXT.search(question)):
        return None
    language = reply_language(question)
    if language == "en" and "english" not in question.casefold() and _ROMAN_INTENT.search(question):
        language = "ur-Latn"
    copy = _COPY[language]

    if follow_up:
        history = _records(data.get("recent_chat"))
        prior = history[-1] if history else {}
        previous_question = prior.get("question")
        if not isinstance(previous_question, str) or not _COMPARE.search(previous_question):
            return None
        reply = prior.get("response")
        ordered = _mentioned(reply, catalog) if isinstance(reply, str) else []
        if len(ordered) < 2:
            return copy["need_choice"]
        named = [ordered[0 if follow_up.group(1).casefold() == "first" else 1]]

    profile = data.get("profile")
    if not isinstance(profile, dict) or not profile:
        return copy["need_profile"]
    if compare or pathway:
        choices = named if named else options[:2]
        if compare and (len(choices) < 2 or (not named and not _TOP_OPTIONS.search(question))):
            return copy["need_two"].format(count=len(options))
        if choices:
            intro = copy["compare"] if compare else copy["options"]
            program = profile.get("class_degree")
            if pathway and not compare and isinstance(program, str) and program.strip():
                intro = copy["program"].format(program=program.strip())
            school = education_stage(profile.get("academic_level")) == "school"
            rows = []
            for row in choices[:2]:
                if row in options:
                    summary = _summary(row, copy)
                    advice = "" if school else _stage_advice(profile, row, copy)
                    rows.append("- " + " ".join(filter(None, (summary, advice))))
                else:
                    rows.append("- " + copy["no_match"].format(title=_title(row)))
            next_step = copy["school_next"] if school else copy["compare_next"]
            return "\n".join([intro, *rows, next_step])
    target = next(iter(named), None) or next(
        (row for row in options if _title(row) == _title(selected)),
        selected or next(iter(options), {}),
    )
    if not _title(target):
        return copy["need_profile"]
    if skills:
        return _skill_answer(data, target, selected, copy)
    if target not in options:
        return copy["no_match"].format(title=_title(target))
    return " ".join(filter(None, (_summary(target, copy), _stage_advice(profile, target, copy))))
