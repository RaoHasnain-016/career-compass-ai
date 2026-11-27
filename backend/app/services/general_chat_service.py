"""Answer common learning questions and simple calculations locally."""

from decimal import Decimal, ROUND_HALF_UP
import re

from app.services.local_chat_service import reply_language


_NUMBER = r"\d{1,9}(?:\.\d{1,6})?"
_MARKS = re.compile(
    rf"(?:what is |calculate |i got |i scored )?({_NUMBER})\s*(?:out of|/)\s*({_NUMBER})"
    r"(?:\s*[,;–-]?\s*(?:as (?:a )?percentage|what is my percentage|percentage|marks))?"
)
_PERCENT = re.compile(rf"(?:what is |calculate )?({_NUMBER})\s*%\s+of\s+({_NUMBER})")
_CONCEPT = re.compile(
    r"(?:what (?:is|are)|explain|tell me about|define) (?:a |an )?(.+)"
    r"|(.+) (?:kya hai|kya hoti hai|samjhao)"
    r"|(.+) (?:کیا ہے|کیا ہوتی ہے|سمجھائیں)"
)
_ALIASES = {
    "artificial intelligence": "ai",
    "مصنوعی ذہانت": "ai",
    "پائتھن": "python",
    "cv": "resume",
    "résumé": "resume",
    "سی وی": "resume",
    "انٹرن شپ": "internship",
    "ڈیٹا اینالیسس": "data analysis",
}
_EXPLANATIONS = {
    "python": (
        "Python is a programming language used for automation, data analysis and building applications. A good first exercise is to write a short program that asks for your name and prints a greeting.",
        "پائتھن ایک پروگرامنگ زبان ہے۔ اسے کام خودکار بنانے، ڈیٹا سمجھنے اور ایپس بنانے کے لیے استعمال کیا جاتا ہے۔ شروعات کے لیے ایک چھوٹا پروگرام بنائیں جو آپ کا نام پوچھے اور سلام لکھے۔",
        "Python ek programming language hai. Is se kaam automate kar sakte hain, data samajh sakte hain aur apps bana sakte hain. Pehli practice ke liye naam poochne aur salam print karne wala chhota program banayein.",
    ),
    "ai": (
        "AI is software that can perform tasks such as recognizing patterns, generating text or suggesting options. Its answers can be wrong, so check important claims against a reliable source.",
        "مصنوعی ذہانت ایسا سافٹ ویئر ہے جو پیٹرن پہچان سکتا ہے، متن بنا سکتا ہے یا تجاویز دے سکتا ہے۔ اہم معلومات کو کسی معتبر ذریعے سے ضرور جانچیں۔",
        "AI aisa software hai jo patterns pehchan sakta hai, text likh sakta hai aur suggestions de sakta hai. Zaroori maloomat kisi bharosemand source se check karein.",
    ),
    "resume": (
        "A résumé or CV summarizes your education, skills, projects and relevant experience. Start with the role you want, then pick two examples that show how you used the skills it needs.",
        "سی وی میں آپ کی تعلیم، مہارتیں، پروجیکٹس اور متعلقہ تجربہ درج ہوتا ہے۔ جس کام کے لیے درخواست دے رہے ہیں، اس سے متعلق دو اچھی مثالیں منتخب کریں۔",
        "CV mein aap ki taleem, skills, projects aur relevant experience ka khulasa hota hai. Jis role ke liye apply karna hai, us ki skills dikhane wali do misaalein chunein.",
    ),
    "internship": (
        "An internship gives you a chance to learn how a field works through practical experience. Look for a role with clear learning tasks, then tailor your CV to those tasks.",
        "انٹرن شپ میں آپ کسی شعبے کو عملی کام کے ذریعے سمجھتے ہیں۔ ایسا موقع تلاش کریں جس میں سیکھنے کے کام واضح ہوں، اور اپنی سی وی اسی کے مطابق تیار کریں۔",
        "Internship mein aap kisi field ko practical kaam se samajhte hain. Aisa role dekhein jahan seekhne ke tasks wazeh hon, phir apni CV un ke mutabiq banayein.",
    ),
    "data analysis": (
        "Data analysis means using data to answer a question. Try a small spreadsheet first. Check missing entries, summarize one column and make one chart that answers your question.",
        "ڈیٹا اینالیسس میں آپ ڈیٹا کی مدد سے کسی سوال کا جواب نکالتے ہیں۔ ایک چھوٹی اسپریڈشیٹ میں خالی اندراج دیکھیں، ایک کالم کا خلاصہ کریں اور ایک چارٹ بنائیں۔",
        "Data analysis ka matlab data se kisi sawal ka jawab nikalna hai. Chhoti spreadsheet lein, khaali entries dekhein, ek column ka khulasa karein aur ek chart banayein.",
    ),
}
_LANGUAGE_INDEX = {"en": 0, "ur": 1, "ur-Latn": 2}


def _number(value):
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(rounded, "f").rstrip("0").rstrip(".")


def answer_general_question(question):
    """Return a grounded answer for a supported standalone question."""
    text = " ".join(question.casefold().strip().strip("?!؟.").split())
    if match := _MARKS.fullmatch(text):
        score, total = map(Decimal, match.groups())
        if total == 0:
            return "The total cannot be zero when calculating a percentage. What was the maximum possible score?"
        return f"**{_number(score / total * 100)}%**. Calculation: {score} ÷ {total} × 100."
    if match := _PERCENT.fullmatch(text):
        percent, amount = map(Decimal, match.groups())
        return f"**{_number(percent * amount / 100)}**. Calculation: {amount} × {percent} ÷ 100."

    match = _CONCEPT.fullmatch(text)
    if match is None:
        return None
    term = next(group for group in match.groups() if group is not None)
    explanations = _EXPLANATIONS.get(_ALIASES.get(term, term))
    language = "ur-Latn" if match.group(2) is not None else reply_language(question)
    return explanations[_LANGUAGE_INDEX[language]] if explanations else None
