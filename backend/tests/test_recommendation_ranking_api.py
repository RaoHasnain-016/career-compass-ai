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
        self.profile = routes.StudentProfile(user_id=user_id)
        self.rows = []
        for title, score in [("Software Engineer", 70.5), ("IT Support Technician", 55)]:
            career = routes.Career(career_id=uuid4(), title=title)
            self.rows.append(routes.Recommendation(
                recommendation_id=uuid4(), career=career, user_id=user_id, match_score=score,
            ))

        self.db = Mock()
        recommendations = Mock()
        recommendations.options.return_value.filter.return_value.order_by.return_value.all.return_value = self.rows
        profile = Mock()
        profile.filter.return_value.first.return_value = self.profile
        self.db.query.side_effect = {
            routes.Recommendation: recommendations,
            routes.StudentProfile: profile,
        }.__getitem__

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
