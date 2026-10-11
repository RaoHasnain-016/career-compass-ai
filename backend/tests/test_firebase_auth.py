"""Run from backend with: python -m unittest discover -s tests -v."""

import os
import unittest
from unittest.mock import patch

import firebase_admin
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from firebase_admin import auth
from google.auth.exceptions import TransportError
from requests.exceptions import ConnectionError, Timeout

# These tests do not load service-account credentials or contact Firebase.
with patch.dict(os.environ, {"FIREBASE_CREDENTIALS_PATH": "unused-in-tests.json"}):
    with patch.dict(firebase_admin._apps, {"[DEFAULT]": object()}):
        from app.utils.auth_dependency import get_current_firebase_user


class FirebaseAuthenticationTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_firebase_user)):
            return user

        self.client = TestClient(app)
        self.verify = patch(
            "app.services.firebase_service.auth.verify_id_token"
        ).start()
        self.addCleanup(patch.stopall)
        self.addCleanup(self.client.close)

    def request(self, token="test-token"):
        return self.client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

    def test_verification_outages_return_retryable_503_without_internal_details(self):
        internal_details = "private-network-host: [WinError 10013] socket blocked"
        failures = (
            ConnectionError(internal_details),
            Timeout(internal_details),
            TransportError(internal_details),
            auth.CertificateFetchError(internal_details, cause=None),
        )
        for failure in failures:
            with self.subTest(error=type(failure).__name__):
                self.verify.side_effect = failure
                response = self.request()

                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["Retry-After"], "30")
                self.assertEqual(
                    response.json()["detail"],
                    "Authentication service is temporarily unavailable. "
                    "Please try again shortly.",
                )
                self.assertNotIn(internal_details, response.text)

    def test_invalid_and_expired_tokens_remain_unauthorized(self):
        failures = (
            auth.InvalidIdTokenError("Invalid signature"),
            auth.ExpiredIdTokenError("Token expired", cause=None),
            ValueError("Token must be a non-empty string"),
        )
        for failure in failures:
            with self.subTest(error=type(failure).__name__):
                self.verify.side_effect = failure
                response = self.request()

                self.assertEqual(response.status_code, 401)
                self.assertTrue(
                    response.json()["detail"].startswith("Invalid Firebase token:")
                )
                self.assertNotIn("Retry-After", response.headers)

    def test_valid_token_returns_only_sdk_verified_claims(self):
        verified_claims = {"uid": "verified-user", "email": "test@example.com"}
        self.verify.return_value = verified_claims

        response = self.request("signed-firebase-token")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), verified_claims)
        self.verify.assert_called_once_with("signed-firebase-token")

    def test_missing_and_invalid_authorization_do_not_attempt_verification(self):
        for headers in ({}, {"Authorization": "Basic test-token"}):
            with self.subTest(headers=headers):
                response = self.client.get("/protected", headers=headers)

                self.assertEqual(response.status_code, 401)
                self.verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
