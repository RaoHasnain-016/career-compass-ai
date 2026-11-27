"""Student-update relevance and authenticated API checks with isolated test data."""

from datetime import datetime, timezone
import os
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import firebase_admin
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

with (
    patch.dict(os.environ, {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}),
    patch("dotenv.load_dotenv"),
    patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}),
):
    from app.database import Base
    from app.models import StudentUpdate, StudentUpdateRead, User
    from app.routes import student_update_routes
    from app.services.student_updates_service import (
        UpdateAudience, academic_fields, education_stage, load_audience, news_matches, record_student_update,
    )
    from app.utils.auth_dependency import get_current_firebase_user


class RelevanceTests(unittest.TestCase):
    def test_stage_labels_do_not_confuse_diploma_and_secondary(self):
        for value, expected in {
            "Matric": "school", "Secondary (Class 9–10)": "school",
            "Intermediate": "senior_secondary", "High School Senior": "senior_secondary",
            "Diploma / DAE": "diploma", "Post-secondary vocational certificate": "diploma",
            "Bachelor": "undergraduate", "Postgraduate": "postgraduate",
        }.items():
            with self.subTest(level=value):
                self.assertEqual(education_stage(value), expected)

    def test_department_labels_resolve_to_specific_fields(self):
        self.assertEqual(academic_fields("Computer Science"), ["technology"])
        self.assertEqual(academic_fields("Civil Technology"), ["engineering"])
        self.assertEqual(academic_fields("Health & Science"), ["health", "science"])

    def test_postgraduate_news_only_reaches_eligible_department_and_country(self):
        item = {"fields": ["health"], "stages": ["postgraduate"], "country": "Pakistan"}
        self.assertTrue(news_matches(item, UpdateAudience("postgraduate", "Pakistan", ("health",))))
        for stage in ("school", "diploma", "undergraduate", "exploring"):
            with self.subTest(stage=stage):
                self.assertFalse(news_matches(item, UpdateAudience(stage, "Pakistan", ("health",))))
        self.assertFalse(news_matches(item, UpdateAudience("postgraduate", "Canada", ("health",))))
        self.assertFalse(news_matches(item, UpdateAudience("postgraduate", "Pakistan", ("business",))))

    def test_occupational_research_can_match_as_attributed_foreign_news(self):
        article = {"fields": ["technology"], "stages": [], "country": "United States", "source": "O*NET"}
        self.assertTrue(news_matches(article, UpdateAudience("diploma", "Pakistan", ("technology",))))
        self.assertFalse(news_matches({**article, "fields": []}, UpdateAudience("diploma", "Pakistan", ("technology",))))

    def test_general_admission_announcement_needs_matching_stage_and_country(self):
        article = {"fields": [], "stages": ["undergraduate"], "country": "Pakistan"}
        self.assertTrue(news_matches(article, UpdateAudience("undergraduate", "Pakistan")))
        self.assertFalse(news_matches(article, UpdateAudience("diploma", "Pakistan", ("technology",))))
        self.assertFalse(news_matches(article, UpdateAudience("undergraduate", "Canada", ("technology",))))
        self.assertFalse(news_matches({**article, "country": None}, UpdateAudience("undergraduate", "Pakistan", ("technology",))))

    def test_active_career_excludes_saved_and_recommended_fields(self):
        db = Mock()
        db.scalar.return_value = SimpleNamespace(
            selected_career_id=uuid4(), academic_level="Diploma / DAE", country="Pakistan",
            study_preference="Career direction: Business | Education stream: Commerce",
        )
        db.execute.return_value.one_or_none.return_value = ("Cybersecurity Analyst", "Technology")

        audience = load_audience(db, uuid4())

        self.assertEqual(audience, UpdateAudience("diploma", "Pakistan", ("technology",), "Cybersecurity Analyst"))
        db.scalars.assert_not_called()

    def test_inactive_selection_restores_profile_and_saved_career_fallback(self):
        db = Mock()
        db.scalar.return_value = SimpleNamespace(
            selected_career_id=uuid4(), academic_level="Bachelor", country=None,
            study_preference="Country: Pakistan | Career direction: Law",
        )
        db.execute.return_value.one_or_none.return_value = None
        db.scalars.side_effect = [["Technology"], ["Business"]]

        self.assertEqual(
            load_audience(db, uuid4()),
            UpdateAudience("undergraduate", "Pakistan", ("law", "technology", "business")),
        )

    def test_occupation_specific_news_distinguishes_careers_within_one_field(self):
        article = {"fields": ["technology"], "country": "Pakistan", "stages": []}
        audience = UpdateAudience("diploma", "Pakistan", ("technology",), "Cybersecurity Analyst")

        self.assertTrue(news_matches({**article, "occupations": ["cybersecurity"]}, audience))
        self.assertTrue(news_matches(article, audience))
        self.assertFalse(news_matches({**article, "occupations": ["software"]}, audience))
        self.assertFalse(news_matches({**article, "occupations": ["cybersecurity"], "stages": ["postgraduate"]}, audience))
        self.assertFalse(news_matches({**article, "occupations": ["cybersecurity"], "stages": ["diploma"], "country": "UK"}, audience))


class InboxApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine, tables=[User.__table__, StudentUpdate.__table__, StudentUpdateRead.__table__])
        sessions = sessionmaker(bind=self.engine)
        self.student, self.other, self.admin = uuid4(), uuid4(), uuid4()
        with sessions.begin() as db:
            for uid, user_id, role in [("a", self.student, "student"), ("b", self.other, "Student"), ("staff", self.admin, "admin")]:
                db.add(User(user_id=user_id, firebase_uid=uid, full_name="Synthetic", email=f"{uid}@example.invalid", role=role))
            db.flush()
            record_student_update(db, self.student, category="profile", title="Student A private event", summary="Test event", url="/profile-setup")
            record_student_update(db, self.other, category="profile", title="Student B private event", summary="Test event", url="/profile-setup")

        app = FastAPI()
        app.include_router(student_update_routes.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.assertEqual(self.client.get("/student-updates/notifications").status_code, 401)

        async def fake_token(authorization: str = Header()):
            return {"uid": authorization}

        app.dependency_overrides[get_current_firebase_user] = fake_token
        self.enterContext(patch.object(student_update_routes, "SessionLocal", sessions))
        self.enterContext(patch.object(student_update_routes, "get_audience", return_value=UpdateAudience("diploma", "Pakistan", ("technology",))))
        self.enterContext(patch.object(student_update_routes, "get_career_news", new_callable=AsyncMock, return_value={
            "items": [], "status": "live", "checked_at": datetime.now(timezone.utc).isoformat(),
        }))

    def inbox(self, user):
        response = self.client.get("/student-updates/notifications", headers={"Authorization": user})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        return response.json()

    def test_inbox_is_private_and_mark_read_is_idempotent(self):
        a, b = self.inbox("a"), self.inbox("b")
        a_id = next(item["id"] for item in a["items"] if item["title"] == "Student A private event")
        b_id = next(item["id"] for item in b["items"] if item["title"] == "Student B private event")
        self.assertNotIn(b_id, {item["id"] for item in a["items"]})
        for _ in range(2):
            response = self.client.post("/student-updates/notifications/read", headers={"Authorization": "a"}, json={"ids": [a_id, b_id]})
            self.assertEqual(response.json(), {"unread_count": a["unread_count"] - 1, "read_ids": [a_id]})
        self.assertEqual(self.inbox("b")["unread_count"], b["unread_count"])
        self.assertTrue(next(item for item in self.inbox("a")["items"] if item["id"] == a_id)["read"])

    def test_inbox_selects_news_for_the_active_career_and_excludes_advanced_offers(self):
        audience = UpdateAudience("diploma", "Pakistan", ("technology",), "Cybersecurity Analyst")
        article = {
            "id": "security", "title": "Career news for cybersecurity analysts", "summary": "",
            "url": "https://www.onetcenter.org/whatsnew.html#technology",
            "source": "O*NET Resource Center", "published_at": datetime.now(timezone.utc).isoformat(),
            "country": "United States", "fields": ["technology"], "stages": [],
            "occupations": ["cybersecurity"],
        }
        articles = [
            article,
            {**article, "id": "software", "occupations": ["software"]},
            {**article, "id": "master", "country": "Pakistan", "stages": ["postgraduate"]},
        ]
        with (
            patch.object(student_update_routes, "get_audience", return_value=audience),
            patch.object(student_update_routes, "get_career_news", new_callable=AsyncMock,
                         return_value={"items": articles, "status": "live", "checked_at": None}),
        ):
            response = self.inbox("a")

        self.assertEqual(response["career_focus"], "Cybersecurity Analyst")
        self.assertEqual([item["id"] for item in response["items"] if item["id"].startswith("news:")], ["news:security"])

    def test_student_only_and_study_options_use_the_signed_in_profile(self):
        self.assertEqual(self.client.get("/student-updates/universities", headers={"Authorization": "staff"}).status_code, 403)
        with patch.object(student_update_routes, "get_university_suggestions", new_callable=AsyncMock, return_value={"stage": "diploma"}) as lookup:
            response = self.client.get("/student-updates/universities?stage=postgraduate", headers={"Authorization": "a"})
        self.assertEqual(response.json(), {
            "stage": "diploma", "profile_country": "Pakistan", "profile_field": "technology",
            "admissions_updates": [], "admissions_status": "live",
        })
        lookup.assert_awaited_once_with(country="Pakistan", field="technology", stage="diploma")
