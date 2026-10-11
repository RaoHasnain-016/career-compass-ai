"""Exercise the cloud entrypoint without database or Firebase network access."""

import importlib
import os
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import firebase_admin
from fastapi.testclient import TestClient


class VercelApplicationTests(unittest.TestCase):
    def setUp(self):
        stack = self.enterContext(ExitStack())
        stack.enter_context(patch.dict(os.environ, {
            "VERCEL": "1",
            "DATABASE_AUTO_CREATE": "false",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }))
        stack.enter_context(patch("dotenv.load_dotenv"))
        stack.enter_context(patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}))
        database = importlib.import_module("app.database")
        self.create_tables = stack.enter_context(patch.object(database.Base.metadata, "create_all"))
        self.begin = stack.enter_context(patch.object(database.engine, "begin"))
        self.connect = stack.enter_context(patch.object(database.engine, "connect"))
        self.entrypoint = importlib.import_module("vercel_app")

    def test_cloud_startup_and_health_do_not_mutate_or_connect_to_database(self):
        # Exercise the implicit Vercel default, without an explicit override.
        os.environ.pop("DATABASE_AUTO_CREATE")
        with TestClient(self.entrypoint.app) as client:
            response = client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})
        self.create_tables.assert_not_called()
        self.begin.assert_not_called()
        self.connect.assert_not_called()

    def test_prefixed_auth_and_unknown_api_routes(self):
        with TestClient(self.entrypoint.app) as client:
            self.assertEqual(client.get("/api/auth/me").status_code, 401)
            missing = client.get("/api/does-not-exist")
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.json(), {"detail": "Not Found"})

    def test_public_database_health_failure_hides_connection_details(self):
        self.connect.side_effect = RuntimeError("private-host/password/connection-details")
        with TestClient(self.entrypoint.app) as client:
            response = client.get("/api/db-test")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Database is unavailable."})


if __name__ == "__main__":
    unittest.main()
