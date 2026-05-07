import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
CHATBOT_TIMEOUT_SECONDS = float(os.getenv("CHATBOT_TIMEOUT_SECONDS", "12"))
CHATBOT_MAX_TOKENS = int(os.getenv("CHATBOT_MAX_TOKENS", "420"))
APP_SITE_URL = os.getenv("APP_SITE_URL", "http://localhost:5173")
APP_NAME = os.getenv("APP_NAME", "Career Compass AI")

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)


def safe(value):
    if value is None:
        return "Not available"
    return value


def compact(value, limit=420):
    text = str(safe(value)).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def build_chatbot_context(
    user,
    profile=None,
    recommendations=None,
    selected_career=None,
    roadmap_stages=None,
    learning_resources=None,
    video_courses=None,
    saved_careers=None,
    chat_history=None,
):
    recommendations = recommendations or []
    roadmap_stages = roadmap_stages or []
    learning_resources = learning_resources or []
    video_courses = video_courses or []
    saved_careers = saved_careers or []
    chat_history = chat_history or []

    if profile:
        profile_text = f"""
Student Profile:
- Name: {safe(user.full_name)}
- Email: {safe(user.email)}
- Academic Level: {safe(profile.academic_level)}
- Class/Degree: {safe(profile.class_degree)}
- Marks/CGPA: {safe(profile.marks_cgpa)}
- Favorite Subjects: {safe(profile.favorite_subjects)}
- Weak Subjects: {safe(profile.weak_subjects)}
- Interests: {safe(profile.interests)}
- Current Skills: {safe(profile.skills)}
- Study Preference: {safe(profile.study_preference)}
"""
    else:
        profile_text = """
Student Profile:
Profile is not completed yet.
"""

    if selected_career:
        selected_career_text = f"""
Selected Career:
- Title: {safe(selected_career.title)}
- Field: {safe(selected_career.field)}
- Overview: {compact(selected_career.overview)}
- Required Education: {compact(selected_career.required_education, 260)}
- Required Skills: {safe(selected_career.required_skills)}
- Required Subjects: {safe(selected_career.required_subjects)}
- Future Scope: {compact(selected_career.future_scope, 260)}
- Difficulty Level: {safe(selected_career.difficulty_level)}
"""
    else:
        selected_career_text = """
Selected Career:
No specific career selected in this request.
"""

    recommendations_text = "\n".join(
        [
            f"""
Recommendation:
- Career: {rec.career.title}
- Field: {rec.career.field}
- Match Score: {float(rec.match_score)}%
- Confidence: {safe(rec.confidence_level)}
- Eligibility: {safe(rec.eligibility_status)}
- Matched Skills: {safe(rec.matched_skills)}
- Missing Skills: {safe(rec.missing_skills)}
- Matched Subjects: {safe(rec.matched_subjects)}
- Missing Subjects: {safe(rec.missing_subjects)}
- Explanation: {compact(rec.explanation, 260)}
- Improvement Advice: {compact(rec.improvement_advice, 220)}
"""
            for rec in recommendations
        ]
    ) or "No recommendations generated yet."

    roadmap_text = "\n".join(
        [
            f"""
Roadmap Stage {stage.stage_order}:
- Title: {stage.title}
- Description: {compact(stage.description, 220)}
- Required Skills: {safe(stage.required_skills)}
- Suggested Resources: {safe(stage.suggested_resources)}
"""
            for stage in roadmap_stages
        ]
    ) or "No roadmap found for the selected career."

    learning_resources_text = "\n".join(
        [
            f"""
Curated Resource:
- Title: {res.title}
- Platform: {res.platform}
- Skill: {res.skill}
- Difficulty: {safe(res.difficulty)}
- Type: {safe(res.resource_type)}
- URL: {res.url}
"""
            for res in learning_resources
        ]
    ) or "No curated learning resources found."

    video_courses_text = "\n".join(
        [
            f"""
Video Course:
- Title: {vid.title}
- Channel: {safe(vid.channel_title)}
- Skill: {vid.skill}
- URL: {vid.video_url}
"""
            for vid in video_courses
        ]
    ) or "No video courses found."

    saved_careers_text = "\n".join(
        [
            f"- {saved.career.title} ({saved.career.field})"
            for saved in saved_careers
        ]
    ) or "No saved careers found."

    chat_history_text = "\n".join(
        [
            f"Student: {msg.question}\nAssistant: {msg.response}"
            for msg in chat_history[-5:]
        ]
    ) or "No previous chat history."

    return f"""
You are working inside Career Compass AI.

Website Purpose:
Career Compass AI is an AI-based career guidance web application for students. It helps students choose suitable careers, understand roadmaps, find missing skills, and get free learning resources and video courses.

Important Rules:
- Use the provided website/database context only.
- Do not guarantee admission, job, salary, or career success.
- Give advisory guidance only.
- If the profile is missing, ask the student to complete the profile.
- If recommendations are missing, ask the student to generate recommendations.
- If roadmap is missing, say roadmap data is not available yet.
- Give practical step-by-step answers.
- Explain career suitability using profile, skills, subjects, interests, and recommendations.
- Mention missing skills and what to learn first.
- Keep answers student-friendly and easy to understand.
- Keep replies concise and fast to read.
- Format every reply with short sections, bullets, or numbered steps.
- Prefer this structure when useful:
  **Quick Answer**
  **Why This Matters**
  **Next Steps**
- Do not answer unrelated questions deeply. Bring the user back to career guidance.

{profile_text}

{selected_career_text}

Top User Recommendations:
{recommendations_text}

Selected Career Roadmap:
{roadmap_text}

Curated Learning Resources:
{learning_resources_text}

Recommended Video Courses:
{video_courses_text}

Saved Careers:
{saved_careers_text}

Recent Chat History:
{chat_history_text}
"""


def ask_career_chatbot(user_message: str, context: str):
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        return "Chatbot API key is not configured. Please add OPENROUTER_API_KEY in backend .env file."

    try:
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            extra_headers={
                "HTTP-Referer": APP_SITE_URL,
                "X-Title": APP_NAME,
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Career Compass AI, an advanced personalized career guidance assistant. "
                        "You must answer using the user's website data, profile, recommendations, roadmap, "
                        "resources, videos, and saved careers. Be practical and accurate. "
                        "Reply in a clean format with short headings, bullets, and numbered steps. "
                        "Keep most answers under 160 words unless the student asks for details."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Website/User Context:
{context}

Student Question:
{user_message}
""",
                },
            ],
            temperature=0.35,
            max_tokens=CHATBOT_MAX_TOKENS,
            timeout=CHATBOT_TIMEOUT_SECONDS,
        )

        return completion.choices[0].message.content
    except Exception:
        return (
            "I can still guide you with your Career Compass AI data, but the external AI provider "
            "is temporarily unavailable. Please check that your profile and recommendations are generated. "
            "Start with your top recommended career, review its missing skills, open the roadmap, and use "
            "the Learning Resources page to study the first missing skill. Then ask again after the AI "
            "provider connection is restored."
        )
