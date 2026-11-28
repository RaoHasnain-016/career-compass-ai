"""Exercise private, reversible feedback through the route with a SQLite test DB."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

import firebase_admin
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

with (
    patch.dict("os.environ", {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}),
    patch("dotenv.load_dotenv"),
    patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}),
):
    from app.routes import recommendation_routes as routes


class RecommendationFeedbackApiTests(TestCase):
    def setUp(self):
        self.student_ids = {"student-a": uuid4(), "student-b": uuid4()}
        self.career_id = uuid4()
        engine = create_engine(
            "sqlite+pysqlite:///:memory:", poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        self.addCleanup(engine.dispose)
        self.engine = engine
        with engine.begin() as connection:
            # Production models include PostgreSQL-only arrays. These minimal
            # fixtures implement the fields the feedback endpoint reads.
            connection.exec_driver_sql("CREATE TABLE users (user_id CHAR(32) PRIMARY KEY)")
            connection.exec_driver_sql("CREATE TABLE careers (career_id CHAR(32) PRIMARY KEY, status BOOLEAN)")
            connection.exec_driver_sql("CREATE TABLE recommendations (user_id CHAR(32), career_id CHAR(32))")
            connection.exec_driver_sql("INSERT INTO careers VALUES (?, 1)", (self.career_id.hex,))
            for student_id in self.student_ids.values():
                connection.exec_driver_sql("INSERT INTO users VALUES (?)", (student_id.hex,))
            connection.exec_driver_sql(
                "INSERT INTO recommendations VALUES (?, ?)",
                (self.student_ids["student-a"].hex, self.career_id.hex),
            )
            routes.RecommendationFeedback.__table__.create(connection)

        def session():
            with Session(engine) as db:
                yield db

        def test_identity(request: Request):
            return {"uid": request.headers["X-Test-Student"]}

        app = FastAPI()
        app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = session
        app.dependency_overrides[routes.get_current_firebase_user] = test_identity
        self.enterContext(patch.object(routes, "get_current_db_user", side_effect=lambda identity, db: (
            SimpleNamespace(user_id=self.student_ids[identity["uid"]])
        )))
        self.client = self.enterContext(TestClient(app))

    def put(self, body, student="student-a"):
        return self.client.put(
            f"/recommendations/{self.career_id}/feedback",
            json=body, headers={"X-Test-Student": student},
        )

    def saved_feedback(self, student):
        with Session(self.engine) as session:
            return routes.get_ranking_feedback(session, self.student_ids[student])

    def test_update_is_idempotent_and_clear_is_reversible(self):
        for feedback in ("helpful", "less_relevant", "less_relevant"):
            response = self.put({"feedback": feedback})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"career_id": str(self.career_id), "feedback": feedback})
        self.assertEqual(self.saved_feedback("student-a"), {self.career_id: "less_relevant"})
        for _ in range(2):
            self.assertEqual(self.put({"feedback": None}).status_code, 200)
        self.assertEqual(self.saved_feedback("student-a"), {})

    def test_other_student_cannot_write_or_erase_feedback(self):
        self.assertEqual(self.put({"feedback": "helpful"}).status_code, 200)
        self.assertEqual(self.put({"feedback": "less_relevant"}, "student-b").status_code, 404)
        self.assertEqual(self.put({"feedback": None}, "student-b").status_code, 200)
        self.assertEqual(self.saved_feedback("student-a"), {self.career_id: "helpful"})
        self.assertEqual(self.saved_feedback("student-b"), {})

    def test_archived_career_requires_clear_and_feedback_must_be_explicit(self):
        self.assertEqual(self.put({}).status_code, 422)
        self.assertEqual(self.put({"feedback": "unknown"}).status_code, 422)
        self.assertEqual(self.put({"feedback": "helpful"}).status_code, 200)
        with self.engine.begin() as connection:
            connection.exec_driver_sql("UPDATE careers SET status = 0")
        self.assertEqual(self.put({"feedback": "less_relevant"}).status_code, 404)
        self.assertEqual(self.put({"feedback": None}).status_code, 200)
        self.assertEqual(self.saved_feedback("student-a"), {})
