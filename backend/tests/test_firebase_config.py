"""Firebase startup configuration without secrets, credential files, or network calls."""

import json
import os
from pathlib import Path
import runpy
import traceback
import unittest
from unittest.mock import patch

import firebase_admin


SERVICE_PATH = Path(__file__).resolve().parents[1] / "app/services/firebase_service.py"


class FirebaseConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

        self.apps = patch.dict(firebase_admin._apps, {}, clear=True)
        self.apps.start()
        self.addCleanup(self.apps.stop)

        # Do not read the developer's .env or any real service-account file.
        self.dotenv = patch("dotenv.load_dotenv").start()
        self.certificate = patch("firebase_admin.credentials.Certificate").start()
        self.initialize = patch("firebase_admin.initialize_app").start()
        self.addCleanup(patch.stopall)

    def load_service(self):
        return runpy.run_path(str(SERVICE_PATH))

    def test_json_credentials_take_precedence_over_local_file(self):
        account = {"type": "service_account", "private_key": "fake-key\nsecond-line"}
        os.environ["FIREBASE_CREDENTIALS_JSON"] = json.dumps(account)
        os.environ["FIREBASE_CREDENTIALS_PATH"] = "unused-local-file.json"

        self.load_service()

        self.certificate.assert_called_once_with(account)
        self.initialize.assert_called_once_with(self.certificate.return_value)

    def test_local_file_remains_supported(self):
        os.environ["FIREBASE_CREDENTIALS_PATH"] = "local-service-account.json"

        self.load_service()

        self.certificate.assert_called_once_with("local-service-account.json")
        self.initialize.assert_called_once_with(self.certificate.return_value)

    def test_empty_json_environment_uses_local_file(self):
        os.environ["FIREBASE_CREDENTIALS_JSON"] = ""
        os.environ["FIREBASE_CREDENTIALS_PATH"] = "local-service-account.json"

        self.load_service()

        self.certificate.assert_called_once_with("local-service-account.json")

    def test_missing_credentials_have_actionable_error(self):
        with self.assertRaisesRegex(
            ValueError, "Set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH"
        ):
            self.load_service()

        self.certificate.assert_not_called()
        self.initialize.assert_not_called()

    def test_initialized_sdk_does_not_require_credentials(self):
        firebase_admin._apps["[DEFAULT]"] = object()

        self.load_service()

        self.certificate.assert_not_called()
        self.initialize.assert_not_called()

    def test_malformed_json_does_not_fall_back_or_disclose_input(self):
        secret_marker = "private-key-placeholder"
        os.environ["FIREBASE_CREDENTIALS_JSON"] = "{" + secret_marker
        os.environ["FIREBASE_CREDENTIALS_PATH"] = "unused-local-file.json"

        try:
            self.load_service()
        except ValueError as error:
            self.assertIn("must contain valid service-account JSON", str(error))
            self.assertNotIn(secret_marker, traceback.format_exc())
            self.assertTrue(error.__suppress_context__)
        else:
            self.fail("Malformed credential JSON was accepted")

        self.certificate.assert_not_called()
        self.initialize.assert_not_called()

    def test_non_object_json_is_rejected_before_sdk_initialization(self):
        for value in ([], None, "fake-private-key", 123):
            with self.subTest(value=value):
                os.environ["FIREBASE_CREDENTIALS_JSON"] = json.dumps(value)
                with self.assertRaisesRegex(ValueError, "service-account JSON object"):
                    self.load_service()

        self.certificate.assert_not_called()
        self.initialize.assert_not_called()

    def test_invalid_service_account_errors_do_not_disclose_secrets(self):
        os.environ["FIREBASE_CREDENTIALS_JSON"] = "{}"
        secret_marker = "private-key-placeholder"
        self.certificate.side_effect = ValueError(secret_marker)

        try:
            self.load_service()
        except ValueError as error:
            self.assertIn("invalid service-account credentials", str(error))
            self.assertNotIn(secret_marker, traceback.format_exc())
            self.assertTrue(error.__suppress_context__)
        else:
            self.fail("Invalid service-account credentials were accepted")

        self.initialize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
