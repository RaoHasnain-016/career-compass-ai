"""Exercise the recommendation ranking opt-in through the HTTP boundary."""

import os
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import firebase_admin
from fastapi import FastAPI
from fastapi.testclient import TestClient

with (
    patch.dict(os.environ, {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}),
    patch("dotenv.load_dotenv"),
    patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}),
):
    from app.routes import recommendation_routes as routes


class RecommendationRankingApiTests(unittest.TestCase):
    def setUp(self):
        user_id = uuid4()
        self.user_id = user_id
        self.profile = routes.StudentProfile(user_id=user_id)
        self.rows = []
        for title, score, field in [("Software Engineer", 70.5, "Technology"), ("IT Support Technician", 55, "Technology")]:
            career = routes.Career(career_id=uuid4(), title=title, status=True, field=field)
            self.rows.append(routes.Recommendation(
                recommendation_id=uuid4(), career=career, career_id=career.career_id,
                user_id=user_id, match_score=score, eligibility_status="eligible",
            ))

        self.db = Mock()
        recommendations = Mock()
        recommendations.options.return_value.filter.return_value.order_by.return_value.all.return_value = self.rows
        profile = Mock()
        profile.filter.return_value.first.return_value = self.profile
        preferences = Mock()
        self.preference_filter = preferences.select_from.return_value.join.return_value.filter
        self.preference_filter.return_value.all.return_value = []
        queries = {
            (routes.Recommendation,): recommendations,
            (routes.StudentProfile,): profile,
            (routes.SavedCareer.career_id, routes.Career.field): preferences,
        }
        self.db.query.side_effect = lambda *entities: queries[entities]

        app = FastAPI()
        app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = lambda: self.db
        app.dependency_overrides[routes.get_current_firebase_user] = lambda: {"uid": "test-student"}
        self.enterContext(patch.object(routes, "get_current_db_user", return_value=Mock(user_id=user_id)))
        self.model_configured = self.enterContext(patch.object(routes, "ranker_configured", return_value=True))
        self.model = self.enterContext(patch.object(routes, "rank_recommendations"))
        self.client = self.enterContext(TestClient(app))

    def test_default_keeps_rule_order_when_model_is_configured(self):
        response = self.client.get("/recommendations/me")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["model_ranking_available"])
        self.assertEqual(payload["ranking_source"], "rules")
        self.assertEqual([row["match_score"] for row in payload["recommendations"]], [70.5, 55])
        self.assertTrue(all("model_rank" not in row for row in payload["recommendations"]))
        self.model.assert_not_called()
        self.db.query.assert_called_once_with(routes.Recommendation)

    def test_opt_in_preserves_scores_and_adds_model_rank(self):
        self.model.return_value = (list(reversed(self.rows)), "trained")
        response = self.client.get("/recommendations/me?ranking=model")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ranking_source"], "trained")
        self.assertEqual([(row["model_rank"], row["match_score"]) for row in payload["recommendations"]], [(1, 55), (2, 70.5)])
        self.model.assert_called_once_with(self.profile, self.rows)
        self.db.commit.assert_not_called()

    def test_opt_in_falls_back_without_configuration(self):
        self.model_configured.return_value = False
        response = self.client.get("/recommendations/me?ranking=model")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["model_ranking_available"])
        self.assertEqual(payload["ranking_source"], "rules")
        self.model.assert_not_called()

    def test_configured_but_unusable_model_preserves_rule_order(self):
        self.model.return_value = (self.rows, "rules")
        response = self.client.get("/recommendations/me?ranking=model")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ranking_source"], "rules")
        self.assertEqual([row["match_score"] for row in payload["recommendations"]], [70.5, 55])
        self.assertTrue(all("model_rank" not in row for row in payload["recommendations"]))

    def test_personalized_order_uses_only_authenticated_students_bookmarks(self):
        self.rows[1].match_score = 68
        self.preference_filter.return_value.all.return_value = [(self.rows[1].career_id, " Technology ")]
        response = self.client.get("/recommendations/me?ranking=personalized")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ranking_source"], "personalized")
        self.assertEqual([row["match_score"] for row in payload["recommendations"]], [68, 70.5])
        self.assertEqual([row["personalization_reason"] for row in payload["recommendations"]], ["saved_career", "saved_field"])
        owner_filter, active_filter = self.preference_filter.call_args.args
        self.assertTrue(owner_filter.compare(routes.SavedCareer.user_id == self.user_id))
        self.assertTrue(active_filter.compare(routes.Career.status.is_(True)))
        self.model.assert_not_called()
        self.db.commit.assert_not_called()

        self.preference_filter.return_value.all.return_value = []
        refreshed = self.client.get("/recommendations/me?ranking=personalized").json()
        self.assertEqual(refreshed["ranking_source"], "rules")
        self.assertEqual([row["match_score"] for row in refreshed["recommendations"]], [70.5, 68])

    def test_aspirational_bookmark_does_not_override_eligibility(self):
        self.rows[0].eligibility_status = "foundation_stage"
        self.preference_filter.return_value.all.return_value = [(self.rows[0].career_id, "Technology")]
        response = self.client.get("/recommendations/me?ranking=personalized")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ranking_source"], "personalized")
        self.assertEqual([row["match_score"] for row in payload["recommendations"]], [55, 70.5])
        self.assertEqual(payload["recommendations"][0]["personalization_reason"], "saved_field")
        self.assertNotIn("personalization_reason", payload["recommendations"][1])
