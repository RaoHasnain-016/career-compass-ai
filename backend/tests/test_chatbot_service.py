"""Run from backend with: python -m unittest discover -s tests -v."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import firebase_admin
import httpx
from fastapi import HTTPException
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

# Import the route without reading credentials, loading .env, or connecting to a
# database. Firebase authentication is exercised in test_firebase_auth.py.
with patch.dict(
    os.environ,
    {
        "OPENROUTER_API_KEY": "test-provider-key",
        "FIREBASE_CREDENTIALS_PATH": "unused-in-tests.json",
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
    },
):
    with patch("dotenv.load_dotenv"), patch.dict(
        firebase_admin._apps, {"[DEFAULT]": object()}
    ):
        from app.routes import chatbot_routes
        from app.schemas.chatbot_schema import ChatbotRequest
        from app.services import chatbot_service


class ChatbotServiceTests(unittest.TestCase):
    def setUp(self):
        self.provider = self.enterContext(patch.object(chatbot_service, "client"))
        self.enterContext(
            patch.object(chatbot_service, "OPENROUTER_API_KEY", "test-provider-key")
        )
        self.create = self.provider.chat.completions.create
        self.request = httpx.Request("POST", "https://provider.invalid/chat")

    def ask(self):
        return chatbot_service.ask_career_chatbot(
            user_message="What should I learn first?",
            context="Student is interested in software development.",
        )

    def assert_service_error(self, expected_status):
        with self.assertRaises(chatbot_service.ChatbotServiceError) as raised:
            self.ask()
        self.assertEqual(raised.exception.status_code, expected_status)
        self.assertTrue(raised.exception.detail.strip())
        self.assertNotIn("private-provider-diagnostic", raised.exception.detail)
        return raised.exception

    def test_success_returns_trimmed_provider_answer_with_student_context(self):
        self.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="  Start with Python basics.\n")
                )
            ]
        )

        self.assertEqual(self.ask(), "Start with Python basics.")
        self.create.assert_called_once()
        messages = self.create.call_args.kwargs["messages"]
        self.assertTrue(any(message["role"] == "system" for message in messages))
        user_messages = "\n".join(
            message["content"] for message in messages if message["role"] == "user"
        )
        self.assertIn("What should I learn first?", user_messages)
        self.assertIn("Student is interested in software development.", user_messages)
        self.assertIn(
            "openrouter/free",
            self.create.call_args.kwargs["extra_body"]["models"],
        )

    def test_unconfigured_provider_is_unavailable_without_making_a_request(self):
        for key in (None, "", "YOUR_OPENROUTER_API_KEY"):
            with self.subTest(key=key), patch.object(
                chatbot_service, "OPENROUTER_API_KEY", key
            ):
                self.assert_service_error(503)
        self.create.assert_not_called()

    def test_multilingual_questions_and_replies_preserve_their_scripts(self):
        exchanges = (
            ("مجھے کون سی مہارت سیکھنی چاہیے؟", "پہلے اپنی بنیادی مہارتوں پر کام کریں۔"),
            ("Mujhe konsi skill seekhni chahiye?", "Pehle apni bunyadi skills behtar karein."),
            ("ما المهارة التي أتعلمها أولاً؟", "ابدأ بالمهارات الأساسية."),
            ("我应该先学习什么技能？", "先学习基础技能。"),
        )
        for question, answer in exchanges:
            with self.subTest(question=question):
                self.create.return_value = SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
                )
                result = chatbot_service.ask_career_chatbot(question, "Student profile context.")

                self.assertEqual(result, answer)
                messages = self.create.call_args.kwargs["messages"]
                self.assertTrue(
                    any(question in item["content"] for item in messages if item["role"] == "user")
                )

    def test_timeout_and_connection_errors_have_retryable_statuses(self):
        failures = (
            (APITimeoutError(request=self.request), 504),
            (
                APIConnectionError(
                    message="private-provider-diagnostic", request=self.request
                ),
                503,
            ),
        )
        for error, expected_status in failures:
            with self.subTest(error=type(error).__name__):
                self.create.side_effect = error
                self.assert_service_error(expected_status)

    def test_provider_status_errors_are_mapped_without_exposing_diagnostics(self):
        for provider_status in (401, 402, 403, 404, 429, 400, 500):
            with self.subTest(provider_status=provider_status):
                error_type = RateLimitError if provider_status == 429 else APIStatusError
                self.create.side_effect = error_type(
                    "private-provider-diagnostic",
                    response=httpx.Response(provider_status, request=self.request),
                    body={"error": "private-provider-diagnostic"},
                )
                expected = 503 if provider_status in (401, 402, 403, 404, 429) else 502
                self.assert_service_error(expected)

    def test_missing_choices_and_empty_answers_are_failures(self):
        malformed_completions = [
            None,
            SimpleNamespace(),
            SimpleNamespace(choices=None),
            SimpleNamespace(choices=[]),
            SimpleNamespace(choices=[SimpleNamespace()]),
            SimpleNamespace(choices=[SimpleNamespace(message=None)]),
        ]
        malformed_completions.extend(
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )
            for content in (None, "", " \n\t ")
        )
        for completion in malformed_completions:
            with self.subTest(completion=completion):
                self.create.return_value = completion
                self.assert_service_error(502)

    def test_unexpected_provider_error_is_a_bad_gateway_response(self):
        self.create.side_effect = RuntimeError("private-provider-diagnostic")
        self.assert_service_error(502)


class ChatbotRouteTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(user_id=uuid4())
        self.db = MagicMock()
        query = self.db.query.return_value
        query.filter.return_value = query
        query.order_by.return_value = query
        query.limit.return_value = query
        query.first.return_value = None
        query.all.return_value = []
        self.enterContext(
            patch.object(chatbot_routes, "get_current_db_user", return_value=self.user)
        )
        self.enterContext(
            patch.object(chatbot_routes, "build_chatbot_context", return_value="context")
        )
        self.ask_provider = self.enterContext(
            patch.object(chatbot_routes, "ask_career_chatbot")
        )

    def ask(self):
        return chatbot_routes.ask_chatbot(
            ChatbotRequest(message="  Help me plan my next step.  "),
            firebase_user={"uid": "test-user"},
            db=self.db,
        )

    def test_provider_failures_return_http_errors_without_saving_chat_history(self):
        for status_code in (502, 503, 504):
            with self.subTest(status_code=status_code):
                self.ask_provider.side_effect = chatbot_service.ChatbotServiceError(
                    status_code=status_code,
                    detail="Chat is temporarily unavailable. Please try again.",
                )

                with self.assertRaises(HTTPException) as raised:
                    self.ask()

                self.assertEqual(raised.exception.status_code, status_code)
                self.assertEqual(
                    raised.exception.detail,
                    "Chat is temporarily unavailable. Please try again.",
                )
                self.db.add.assert_not_called()
                self.db.commit.assert_not_called()
                self.db.refresh.assert_not_called()

    def test_successful_answer_is_saved_and_returned(self):
        self.ask_provider.return_value = "Start by reviewing your missing skills."
        message_id = uuid4()
        self.db.refresh.side_effect = lambda message: setattr(
            message, "message_id", message_id
        )

        response = self.ask()

        self.ask_provider.assert_called_once_with(
            user_message="Help me plan my next step.", context="context"
        )
        self.db.add.assert_called_once()
        saved_message = self.db.add.call_args.args[0]
        self.assertEqual(saved_message.user_id, self.user.user_id)
        self.assertEqual(saved_message.question, "Help me plan my next step.")
        self.assertEqual(saved_message.response, "Start by reviewing your missing skills.")
        self.db.commit.assert_called_once_with()
        self.db.refresh.assert_called_once_with(saved_message)
        self.assertEqual(
            response,
            {
                "message_id": str(message_id),
                "question": "Help me plan my next step.",
                "response": "Start by reviewing your missing skills.",
            },
        )


if __name__ == "__main__":
    unittest.main()
