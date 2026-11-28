"""Curated career guidance with links to the original public references."""

import re

from app.services.local_chat_service import reply_language


_ARTICLES = (
    (
        r"(?:what (?:is|does) (?:a |my )?(?:cv|r[ée]sum[ée])(?: mean)?|(?:how (?:do|can) i |how to )?(?:write|make|improve|update) (?:a |my )?(?:cv|r[ée]sum[ée])|(?:cv|resume) (?:kya hai|kaise banaun|kaise banayein)|سی وی (?:کیا ہے|کیسے بناؤں|کیسے بنائیں))",
        "Writing a CV",
        "UK National Careers Service",
        "https://nationalcareers.service.gov.uk/careers-advice/cv-sections",
        {
            "en": "A CV shows how your education, skills and experience fit a role. Pick one job description, then add two examples from projects, volunteering or work that show the skills it asks for.",
            "ur": "سی وی میں اپنی تعلیم، مہارتیں اور متعلقہ تجربہ مختصر لکھیں۔ ایک ملازمت کی تفصیل دیکھیں اور اس میں مانگی گئی مہارتوں کے لیے اپنے پروجیکٹس، رضاکارانہ کام یا تجربے سے دو مثالیں دیں۔",
            "ur-Latn": "CV mein apni taleem, skills aur relevant tajurba mukhtasar likhein. Ek job description dekhein aur us mein mangi gayi skills ke liye projects, volunteering ya kaam se do misaalein dein.",
        },
    ),
    (
        r"(?:how (?:do|can|should) i prepare for (?:a |my |an )?(?:job )?interview|(?:job )?interview tips|(?:what is|explain) (?:the )?star method|interview ki tayari kaise (?:karun|karein)|انٹرویو کی تیاری کیسے (?:کروں|کریں))",
        "The STAR method for interviews",
        "UK National Careers Service",
        "https://nationalcareers.service.gov.uk/careers-advice/interview-advice/the-star-method",
        {
            "en": "Pick a project that shows a skill the role needs. Practise telling the story with STAR: describe the situation, your task, what you did and what happened as a result.",
            "ur": "اپنے کسی ایسے پروجیکٹ کی مثال چنیں جس میں آپ نے متعلقہ مہارت استعمال کی ہو۔ STAR طریقے سے بتائیں کہ صورتِ حال کیا تھی، آپ کا کام کیا تھا، آپ نے کیا کیا اور اس کا نتیجہ کیا نکلا۔",
            "ur-Latn": "Aisa project chunein jis mein aap ne role se mutalliq skill use ki ho. STAR se practice karein: surat-e-haal, aap ka kaam, aap ne kya kiya aur us ka nateeja kya tha.",
        },
    ),
    (
        r"(?:what is (?:pakistan(?:'s)? )?(?:the )?nvqf|explain (?:the )?nvqf|nvqf kya hai|پاکستان کا ووکیشنل فریم ورک کیا ہے)",
        "Pakistan’s National Vocational Qualifications Framework",
        "NAVTTC",
        "https://navttc.gov.pk/nvqf/",
        {
            "en": "Pakistan’s NVQF describes the skills and training levels behind vocational qualifications. If you are comparing programmes, ask each provider which qualification it awards and what further study it can lead to.",
            "ur": "پاکستان کا فنی تعلیم کا فریم ورک بتاتا ہے کہ ہر سطح کی سند کے لیے کون سی عملی مہارتیں درکار ہیں۔ پروگرام چنتے وقت ادارے سے پوچھیں کہ کون سی سند ملے گی اور اس سے آگے کیا پڑھ سکتے ہیں۔",
            "ur-Latn": "Pakistan ka NVQF batata hai ke har vocational qualification ke liye kis satah ki skills chahiye. Programs compare karte waqt idare se poochhein kaunsi sanad milegi aur us ke baad kya parh sakte hain.",
        },
    ),
    (
        r"(?:what (?:is|does) (?:ibcc equivalence|ssc equivalence|hssc equivalence)(?: mean)?|how (?:do|can) i check (?:my )?(?:ibcc|ssc|hssc) equivalence|(?:ibcc|ssc|hssc) equivalence kya hai|آئی بی سی سی مساوات کیا ہے)",
        "SSC and HSSC equivalence in Pakistan",
        "Inter Boards Coordination Commission",
        "https://ibcc.edu.pk/equivalence-intro/",
        {
            "en": "IBCC assesses whether a qualification is comparable to Pakistan’s SSC or HSSC. Look up your exact qualification with IBCC, then ask the institution you want to apply to which documents it needs.",
            "ur": "آئی بی سی سی یہ جانچتا ہے کہ آپ کی تعلیمی سند پاکستان کی میٹرک یا انٹرمیڈیٹ کی سند کے برابر ہے یا نہیں۔ اپنی مخصوص سند کے لیے آئی بی سی سی کی ہدایات دیکھیں اور متعلقہ ادارے سے مطلوبہ دستاویزات پوچھیں۔",
            "ur-Latn": "IBCC dekhta hai ke aap ki qualification Pakistan ke SSC ya HSSC ke barabar hai ya nahi. Apni exact qualification IBCC par check karein aur jis idare mein jana hai us se zaroori documents poochhein.",
        },
    ),
)

_INDEX = [(re.compile(pattern), title, publisher, url, replies) for pattern, title, publisher, url, replies in _ARTICLES]
_ROMAN_PHRASES = re.compile(r"\b(?:kya hai|kaise karun|kaise karein|kaise banaun|kaise banayein)\b")
_LEAD_IN = re.compile(r"^(?:hi|hello|hey|aoa|salam)(?:\s*[,!،]\s*|\s+)")


def answer_from_knowledge_base(question):
    """Match specific evergreen questions without calling a publisher or model."""
    normalized = " ".join(question.casefold().strip().rstrip("?!؟.۔").split())
    normalized = _LEAD_IN.sub("", normalized)
    for pattern, title, publisher, url, replies in _INDEX:
        if pattern.fullmatch(normalized):
            language = reply_language(question)
            if language == "en" and _ROMAN_PHRASES.search(normalized):
                language = "ur-Latn"
            return replies[language], {
                "status": "reference",
                "checked_at": None,
                "items": [{"title": title, "source": publisher, "url": url}],
            }
    return None
