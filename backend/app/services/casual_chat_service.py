"""Reply locally to complete conversational greetings and courtesies."""

import re
import unicodedata


_ARABIC_MARKS = re.compile(r"[\u0640\u064b-\u065f\u0670\u200c\u200d\ufe0f]")
_ARABIC_LETTERS = str.maketrans("يىك", "ییک")
_PUNCTUATION = re.compile(r"[.!?,؟،۔…-]+")


def _normalize(message):
    text = unicodedata.normalize("NFKC", message).casefold().translate(_ARABIC_LETTERS)
    text = _PUNCTUATION.sub(" ", _ARABIC_MARKS.sub("", text))
    return " ".join(text.strip(" \t\r\n👋😊🙂🙋").split())


_TURNS = (
    (
        ("hi", "hello", "hey", "hiya", "hi there", "hello there", "hey there", "hi bot", "hello chatbot",
         "good morning", "good afternoon", "good evening"),
        "Hi! What would you like to talk about?",
    ),
    (
        ("aoa", "a o a", "salam", "salaam", "assalamualaikum", "assalam alaikum", "assalamu alaikum",
         "assalam o alaikum", "as salamu alaykum", "assalaam alaikum", "assalam o alikum", "salam alaikum",
         "aoa how are you", "aoa kya haal hai", "aoa kaise ho", "aoa kese ho"),
        "Wa alaikum assalam! Aap kis baare mein baat karna chahte hain?",
    ),
    (
        ("السلام علیکم", "اسلام علیکم", "سلام علیکم", "سلام", "السلام علیکم کیسے ہیں"),
        "وعلیکم السلام! آپ آج کس بارے میں بات کرنا چاہتے ہیں؟",
    ),
    (("ہیلو", "ہائے"), "ہیلو! آپ آج کس بارے میں بات کرنا چاہتے ہیں؟"),
    (
        ("how are you", "how are you doing", "how are u", "how r you", "how r u", "hi how are you",
         "what's up", "what’s up", "whats up"),
        "I’m here and ready to help. What’s on your mind?",
    ),
    (
        ("kya haal hai", "kia haal hai", "kaise ho", "kaise hain", "kaisay ho", "kese ho", "kesay ho", "kesi ho"),
        "Main yahan hoon, aap ki madad ke liye. Aap kis baare mein baat karna chahte hain?",
    ),
    (
        ("آپ کیسے ہیں", "کیسے ہو", "کیا حال ہے", "کیا حال ہیں"),
        "میں آپ کی مدد کے لیے حاضر ہوں۔ آج کس بارے میں بات کریں؟",
    ),
    (
        ("thanks", "thank you", "thanks a lot", "thank you so much", "thx", "ty"),
        "You’re welcome!",
    ),
    (("shukriya", "shukria", "bohat shukriya", "buhat shukriya"), "Koi baat nahi! Jab chahein poochhein."),
    (("شکریہ", "بہت شکریہ"), "کوئی بات نہیں! جب چاہیں پوچھیں۔"),
    (
        ("who are you", "what are you", "what can you do", "how can you help",
         "how can you help me", "can you help me", "help", "help me"),
        "I’m the Career Compass assistant. I can help you compare careers, understand skill gaps, or plan your next step.",
    ),
    (
        ("aap kaun hain", "aap kon hain", "tum kon ho", "tum kaun ho", "meri madad kar sakte ho"),
        "Main Career Compass ka assistant hoon. Career options, skills ya agli taleemi manzil par baat kar sakte hain.",
    ),
    (
        ("آپ کون ہیں", "تم کون ہو", "آپ کیا کر سکتے ہیں", "آپ میری کیسے مدد کر سکتے ہیں"),
        "میں کیریئر کمپاس کا معاون ہوں۔ پیشوں کے موازنے، نئی مہارتوں اور پڑھائی کے اگلے قدم میں مدد کر سکتا ہوں۔",
    ),
    (("bye", "goodbye", "see you", "see you later"), "Take care! Come back anytime."),
    (("allah hafiz", "allah hafeez", "khuda hafiz"), "Allah hafiz! Apna khayal rakhein."),
    (("اللہ حافظ", "خدا حافظ"), "اللہ حافظ! اپنا خیال رکھیے۔"),
)

_REPLIES = {_normalize(phrase): reply for phrases, reply in _TURNS for phrase in phrases}


def answer_casual_chat(question: str) -> str | None:
    """Match the whole turn so a greeting cannot hide a substantive question."""
    return _REPLIES.get(_normalize(question))
