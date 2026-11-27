from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from uuid import uuid4

import firebase_admin

# This route is tested with synthetic claims and no Firebase credential file.
with patch("dotenv.load_dotenv"), patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}):
    from app.routes import chatbot_routes
from app.schemas.chatbot_schema import ChatbotRequest
from app.services import chatbot_knowledge_service as service
from app.services.student_updates_service import UpdateAudience


class ChatKnowledgeTests(IsolatedAsyncioTestCase):
    def test_questions_select_the_correct_source(self):
        self.assertEqual(service.knowledge_topic("Which universities should I consider?"), "study_options")
        self.assertEqual(service.knowledge_topic("What is the admissions deadline?"), "admissions")
        self.assertEqual(service.knowledge_topic("Can I apply this Friday from the update in the app?"), "admissions")
        self.assertEqual(service.knowledge_topic("Latest career news?"), "career_news")
        self.assertIsNone(service.knowledge_topic("How do I learn Python?"))

    async def test_mathematics_school_student_gets_pathways_instead_of_degree_notices(self):
        audience = UpdateAudience("school", "Pakistan", ("engineering",))
        option = {
            "title": "SSC and HSSC qualification guidance", "institution": "IBCC", "country": "Pakistan",
            "url": "https://ibcc.edu.pk/faqs/international-qualification-faqs/",
            "note": "Confirm subject groups", "checked_at": "2026-11-27T00:00:00+00:00",
            "verification_status": "verified",
        }
        with patch.object(service, "get_university_suggestions", AsyncMock(return_value={
            "domestic": [option], "international": [], "sources": [option], "checked_at": option["checked_at"],
        })), patch.object(service, "get_career_news", AsyncMock()) as news:
            evidence = await service.retrieve_chat_evidence("admissions", audience)
        news.assert_not_awaited()
        self.assertEqual(evidence["status"], "school_pathway")
        self.assertEqual([item["url"] for item in evidence["items"]], [option["url"]])
        self.assertIn("senior-secondary", service.evidence_only_answer(evidence))

    async def test_news_respects_stage_country_and_field_and_preserves_source_date(self):
        base = {
            "title": "Scholarship applications", "summary": "Read the entry criteria",
            "url": "https://www.hec.gov.pk/english/HECAnnouncements/Pages/Announcements.aspx",
            "source": "Higher Education Commission Pakistan", "published_at": "2026-11-20T00:00:00+00:00",
            "country": "Pakistan", "fields": ["engineering"], "stages": ["undergraduate"],
        }
        feed = {"items": [
            base, {**base, "title": "Other country scholarship", "country": "Canada"},
            {**base, "title": "Other stage scholarship", "stages": ["postgraduate"]},
            {**base, "title": "Other field scholarship", "fields": ["health"]},
        ], "status": "live", "checked_at": "2026-11-27T00:00:00+00:00"}
        with patch.object(service, "get_career_news", AsyncMock(return_value=feed)):
            evidence = await service.retrieve_chat_evidence("admissions", UpdateAudience("undergraduate", "Pakistan", ("engineering",)))
        self.assertEqual([item["title"] for item in evidence["items"]], ["Scholarship applications"])
        self.assertEqual(evidence["items"][0]["published_at"], base["published_at"])
        self.assertIn("confirm the current deadline", service.evidence_only_answer(evidence))


class OfflineChatRouteTests(TestCase):
    def test_hosted_chat_can_answer_an_admissions_question_from_official_sources(self):
        db = MagicMock()
        query = db.query.return_value
        query.filter.return_value = query.order_by.return_value = query.limit.return_value = query
        query.first.return_value = SimpleNamespace(selected_career_id=None, academic_level="Diploma / DAE")
        query.all.return_value = []
        db.refresh.side_effect = lambda message: setattr(message, "message_id", uuid4())
        audience = UpdateAudience("diploma", "Pakistan", ("engineering",))
        evidence = service.empty_evidence("admissions", "diploma", "offline")
        with (
            patch.object(chatbot_routes, "CHATBOT_PROVIDER", "openrouter"),
            patch.dict("os.environ", {"CHATBOT_LIVE_KNOWLEDGE": "1"}),
            patch.object(chatbot_routes, "get_current_db_user", return_value=SimpleNamespace(user_id=uuid4())),
            patch.object(chatbot_routes, "load_audience", return_value=audience),
            patch.object(chatbot_routes.from_thread, "run", return_value=evidence) as live_source,
            patch.object(chatbot_routes, "ask_career_chatbot") as chat_model,
        ):
            response = chatbot_routes.ask_chatbot(ChatbotRequest(message="Are university admissions open?"), {"uid": "synthetic"}, db)
        live_source.assert_called_once_with(chatbot_routes.retrieve_chat_evidence, "admissions", audience)
        chat_model.assert_not_called()
        self.assertEqual(response["reply_mode"], "official_sources")

    def test_current_admissions_does_not_use_external_sources_when_offline(self):
        db = MagicMock()
        query = db.query.return_value
        query.filter.return_value = query.order_by.return_value = query.limit.return_value = query
        query.first.return_value = SimpleNamespace(selected_career_id=None, academic_level="Diploma / DAE")
        query.all.return_value = []
        db.refresh.side_effect = lambda message: setattr(message, "message_id", uuid4())
        with patch.object(chatbot_routes, "CHATBOT_PROVIDER", "local"), patch.dict("os.environ", {
            "CHATBOT_LIVE_KNOWLEDGE": "0", "CAREER_RANKER_DIR": "",
        }), patch.object(chatbot_routes, "get_current_db_user", return_value=SimpleNamespace(user_id=uuid4())), \
                patch.object(chatbot_routes.from_thread, "run") as live_source, \
                patch.object(chatbot_routes, "ask_career_chatbot") as chat_model:
            response = chatbot_routes.ask_chatbot(ChatbotRequest(message="Are university admissions open?"), {"uid": "synthetic"}, db)
        live_source.assert_not_called()
        chat_model.assert_not_called()
        db.rollback.assert_called_once()
        self.assertEqual(response["sources"], [])
        self.assertEqual(response["source_status"], "offline")
        self.assertIn("couldn't verify", response["response"])
