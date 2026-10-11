"""Context regressions: retain useful guidance data without growing prompts."""

import json
import os
import unittest
from decimal import Decimal
from types import SimpleNamespace as Record
from unittest.mock import patch

with patch("dotenv.load_dotenv"), patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
    from app.services.chatbot_service import build_chatbot_context


class ChatbotContextTests(unittest.TestCase):
    def setUp(self):
        self.user = Record(full_name="Private Student", email="private@example.com")
        self.career = Record(
            title="Software Developer", field="Technology", overview="Build applications.",
            required_education="BS Computer Science", required_skills=["Python", "SQL"],
            required_subjects=["Mathematics"], future_scope="Software products",
            difficulty_level="Intermediate",
        )

    def test_guidance_keeps_profile_eligibility_gaps_and_education_without_identity(self):
        profile = Record(
            academic_level="University", class_degree="BSCS", marks_cgpa=Decimal("3.50"),
            favorite_subjects=["Mathematics"], weak_subjects=["Physics"],
            interests=["مصنوعی ذہانت"], skills=["Python"], study_preference="Online",
        )
        recommendation = Record(
            career=self.career, match_score=Decimal("85.50"), confidence_level="High",
            eligibility_status="Eligible", matched_skills=["Python"], missing_skills=["SQL"],
            matched_subjects=["Mathematics"], missing_subjects=["Statistics"],
            explanation="Your coding skills match.", improvement_advice="Learn SQL first.",
        )
        raw = build_chatbot_context(
            self.user, profile=profile, recommendations=[recommendation],
            selected_career=self.career,
        )
        context = json.loads(raw)

        for name, value in vars(profile).items():
            self.assertEqual(context["profile"][name], str(value) if isinstance(value, Decimal) else value)
        selected = context["selected_career"]
        self.assertEqual(selected["required_education"], "BS Computer Science")
        self.assertEqual(selected["required_skills"], ["Python", "SQL"])
        self.assertEqual(selected["required_subjects"], ["Mathematics"])
        rec = context["recommendations"][0]
        self.assertEqual(rec["match_score"], 85.5)
        self.assertEqual(rec["eligibility_status"], "Eligible")
        self.assertEqual(rec["missing_skills"], ["SQL"])
        self.assertEqual(rec["missing_subjects"], ["Statistics"])
        self.assertEqual(rec["improvement_advice"], "Learn SQL first.")
        self.assertIn("مصنوعی ذہانت", raw)
        self.assertNotIn(self.user.full_name, raw)
        self.assertNotIn(self.user.email, raw)
        self.assertNotIn("Important Rules", raw)

    def test_roadmap_and_resource_links_are_not_truncated(self):
        link = "https://example.com/course?lesson=" + "a" * 600
        stage = Record(stage_order=1, title="Start SQL", description="Practice queries.",
                       required_skills=["SQL"], suggested_resources=[link])
        resource = Record(title="SQL course", platform="Example", skill="SQL",
                          difficulty="Beginner", resource_type="Course", url=link)
        video = Record(title="SQL video", channel_title="Example", skill="SQL", video_url=link)
        context = json.loads(build_chatbot_context(
            self.user, roadmap_stages=[stage], learning_resources=[resource], video_courses=[video],
        ))

        self.assertEqual(context["roadmap"][0]["stage_order"], 1)
        self.assertEqual(context["roadmap"][0]["required_skills"], ["SQL"])
        self.assertEqual(context["roadmap"][0]["suggested_resources"], [link])
        self.assertEqual(context["learning_resources"][0]["url"], link)
        self.assertEqual(context["video_courses"][0]["url"], link)

    def test_context_bounds_history_and_recommendations_in_existing_order(self):
        history = [Record(question=f"Question {i}: " + "q" * 1000,
                          response=f"Answer {i}: " + "a" * 3000) for i in range(8)]
        recommendations = [Record(career=self.career, match_score=100 - i,
                                  explanation="x" * 5000, missing_skills=["SQL"])
                           for i in range(10)]
        context = json.loads(build_chatbot_context(
            self.user, recommendations=recommendations, chat_history=history,
        ))

        self.assertEqual([rec["match_score"] for rec in context["recommendations"]], [100, 99, 98])
        self.assertEqual(len(context["recent_chat"]), 3)
        for i, exchange in enumerate(context["recent_chat"], start=5):
            self.assertTrue(exchange["question"].startswith(f"Question {i}: "))
            self.assertTrue(exchange["response"].startswith(f"Answer {i}: "))
            self.assertLessEqual(len(exchange["question"]), 303)
            self.assertLessEqual(len(exchange["response"]), 503)
        self.assertLess(len(json.dumps(context)), 5000)

    def test_missing_data_stays_explicit(self):
        context = json.loads(build_chatbot_context(self.user))
        self.assertIsNone(context["profile"])
        self.assertIsNone(context["selected_career"])
        for name in ("recommendations", "roadmap", "learning_resources", "video_courses",
                     "saved_careers", "recent_chat"):
            self.assertEqual(context[name], [])


if __name__ == "__main__":
    unittest.main()
