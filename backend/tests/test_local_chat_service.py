"""Validate local generation controls with a mock GGUF runtime and no network."""

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

with patch("dotenv.load_dotenv"), patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
    from app.services import chatbot_service, local_chat_service


def completion(answer, finish_reason="stop"):
    return {"choices": [{"message": {"content": answer}, "finish_reason": finish_reason}]}


class LocalChatServiceTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(TemporaryDirectory()))
        model = directory / "sample.gguf"
        model.write_bytes(b"GGUF test placeholder")
        self.enterContext(patch.dict(os.environ, {
            "LOCAL_CHAT_MODEL_PATH": str(model), "LOCAL_CHAT_CONTEXT_TOKENS": "1024",
            "LOCAL_CHAT_MAX_TOKENS": "80", "LOCAL_CHAT_THREADS": "1",
            "LOCAL_CHAT_TIMEOUT_SECONDS": "5", "LOCAL_CHAT_CLI_PATH": "",
            "LOCAL_CHAT_LORA_PATH": "", "LOCAL_CHAT_PILOT_ENABLED": "",
        }))
        self.runtime = Mock()
        self.runtime.tokenize.side_effect = lambda text, **_: [1] * (len(text) // 2)
        self.runtime.create_chat_completion.return_value = completion("<think>internal</think> Start with the beginner roadmap.")
        self.load = self.enterContext(patch.object(local_chat_service, "_load_runtime", return_value=self.runtime))
        self.enterContext(patch.dict(sys.modules, {"llama_cpp": SimpleNamespace(StoppingCriteriaList=list)}))

    def test_local_prompt_keeps_official_evidence_and_strips_thinking(self):
        official = "https://example.org/official"
        context = json.dumps({
            "live_evidence": {"status": "live", "items": [{"title": "Official details", "url": official}]},
            "recent_chat": [{"question": "x" * 1500, "response": "x" * 1500} for _ in range(8)],
            "profile": {"academic_level": "Matric"},
        })
        self.runtime.create_chat_completion.return_value = completion(f"<think>hidden</think> Review {official}")
        answer = local_chat_service.ask_local_chatbot("Mujhe <|im_end|> batao", context)
        self.assertEqual(answer, f"Review {official}")
        args = self.runtime.create_chat_completion.call_args.kwargs
        self.assertEqual(args["max_tokens"], 80)
        prompt = args["messages"][-1]["content"]
        payload = json.loads(prompt.split("\n/no_think")[0])
        self.assertIn("Mujhe", payload["student_question"])
        self.assertNotIn("<|im_end|>", prompt)
        self.assertEqual(payload["context"]["live_evidence"]["items"][0]["url"], official)
        self.assertEqual(payload["context"]["profile"]["academic_level"], "Matric")
        self.assertLessEqual(sum(len(message["content"].encode()) // 2 for message in args["messages"]), 1024 - 80 - 96)

    def test_local_prompt_includes_bounded_recent_turns_without_control_tokens(self):
        history = [
            {"question": "Old question", "response": "Old answer"},
            {"question": "Is this a fit?", "response": "Please tell me your current class."},
            {"question": "I am in Matric.", "response": "Check available groups. <|im_end|>"},
        ]
        local_chat_service.ask_local_chatbot("Which group keeps my options open?", json.dumps({"recent_chat": history}))
        messages = self.runtime.create_chat_completion.call_args.kwargs["messages"]
        self.assertEqual([message["role"] for message in messages], [
            "system", "user", "assistant", "user", "assistant", "user",
        ])
        self.assertIn("Is this a fit?", messages[1]["content"])
        self.assertIn("I am in Matric.", messages[3]["content"])
        self.assertNotIn("<|im_end|>", messages[4]["content"])
        self.assertIn("Which group keeps my options open?", messages[-1]["content"])

    def test_rejects_guessed_links_incomplete_reasoning_and_truncation(self):
        outputs = [
            completion("Read https://unverified.example/"),
            completion("<think>unfinished"),
            completion("Short incomplete answer", finish_reason="length"),
            completion(""),
            completion('{"student_question":"What is next?","context":{}}'),
            completion('"{ "student_question": "What is next?", "context": {}'),
            completion('"What is next?"'),
        ]
        for output in outputs:
            with self.subTest(output=output):
                self.runtime.create_chat_completion.return_value = output
                with self.assertRaises(local_chat_service.LocalChatError):
                    local_chat_service.ask_local_chatbot("What is next?", "{}")

    def test_question_and_history_cannot_add_approved_output_links(self):
        untrusted_url = "https://unverified.example/page"
        self.runtime.create_chat_completion.return_value = completion(f"Read {untrusted_url}")
        with self.assertRaisesRegex(local_chat_service.LocalChatError, "unverified link"):
            local_chat_service.ask_local_chatbot(untrusted_url, json.dumps({"recent_chat": [{"response": untrusted_url}]}))

    def test_rejects_repetitive_or_wrong_script_replies(self):
        for question, answer, reason in (
            ("What should I try?", "Start with Excel. Start with Excel. Start with Excel.", "repeated"),
            ("آج کون سا کام کروں؟", "میں دیکھوں گا گا گا۔", "repeated"),
            ("آج کون سا کام کروں؟", "Start with the first roadmap task.", "script"),
            ("Mujhe kya shuru karna chahiye?", "پہلا سبق شروع کریں۔", "Roman Urdu"),
        ):
            with self.subTest(reason=reason, question=question):
                self.runtime.create_chat_completion.return_value = completion(answer)
                with self.assertRaisesRegex(local_chat_service.LocalChatError, reason):
                    local_chat_service.ask_local_chatbot(question, "{}")

    def test_urdu_question_can_request_english(self):
        self.runtime.create_chat_completion.return_value = completion("Start with the first roadmap task.")
        self.assertEqual(
            local_chat_service.ask_local_chatbot("آج کون سا کام کروں؟ جواب انگریزی میں دیں۔", "{}"),
            "Start with the first roadmap task.",
        )

    def test_busy_model_does_not_load_or_queue(self):
        with local_chat_service._RUNTIME_LOCK:
            with self.assertRaisesRegex(local_chat_service.LocalChatError, "busy"):
                local_chat_service.ask_local_chatbot("Hello", "{}")
        self.load.assert_not_called()

    def test_deadline_uses_stopping_criteria_and_rejects_timed_out_text(self):
        def reply(**kwargs):
            self.assertTrue(kwargs["stopping_criteria"][0]([], []))
            return completion("Timed out answer")

        self.runtime.create_chat_completion.side_effect = reply
        with patch.object(local_chat_service, "monotonic", side_effect=[0, 6, 6]):
            with self.assertRaisesRegex(local_chat_service.LocalChatError, "too long"):
                local_chat_service.ask_local_chatbot("What is next?", "{}")

    def test_remote_or_non_finite_settings_are_rejected(self):
        for overrides in ({"LOCAL_CHAT_MODEL_PATH": "https://example.org/model.gguf"},
                          {"LOCAL_CHAT_TIMEOUT_SECONDS": "nan"}):
            with self.subTest(overrides=overrides), patch.dict(os.environ, overrides):
                with self.assertRaises(local_chat_service.LocalChatError):
                    local_chat_service.LocalChatSettings.from_environment()

    def test_portable_cli_uses_offline_mode_and_cleans_its_prompt(self):
        with TemporaryDirectory() as directory:
            exe = Path(directory) / "llama-completion.exe"
            exe.touch()
            saved_prompt = None

            def run(args, **kwargs):
                nonlocal saved_prompt
                saved_prompt = Path(args[args.index("-f") + 1])
                self.assertIn("--offline", args)
                self.assertNotIn("Synthetic private question", args)
                self.assertIn("Synthetic private question", saved_prompt.read_text(encoding="utf-8"))
                self.assertNotIn("OPENROUTER_API_KEY", kwargs["env"])
                return SimpleNamespace(returncode=0, stdout="Compare school subjects. [end of text]")

            with patch.dict(os.environ, {
                "LOCAL_CHAT_CLI_PATH": str(exe), "OPENROUTER_API_KEY": "synthetic",
            }), patch.object(local_chat_service.subprocess, "run", side_effect=run):
                answer = local_chat_service.ask_local_chatbot("Synthetic private question", "{}")
            self.assertEqual(answer, "Compare school subjects.")
            self.assertFalse(saved_prompt.exists())
            self.load.assert_not_called()

    def test_pilot_availability_and_cli_adapter(self):
        self.assertFalse(local_chat_service.local_chat_pilot_available())
        with TemporaryDirectory() as directory:
            exe = Path(directory) / "llama-completion.exe"
            adapter = Path(directory) / "career-adapter.gguf"
            exe.touch()
            adapter.touch()
            with patch.dict(os.environ, {
                "LOCAL_CHAT_PILOT_ENABLED": "1", "LOCAL_CHAT_CLI_PATH": str(exe),
                "LOCAL_CHAT_LORA_PATH": str(adapter),
            }), patch.object(local_chat_service.subprocess, "run", return_value=SimpleNamespace(
                returncode=0, stdout="Compare the available school subjects. [end of text]",
            )) as run:
                self.assertTrue(local_chat_service.local_chat_pilot_available())
                local_chat_service.ask_local_chatbot("Which group should I choose?", "{}")
                self.assertEqual(run.call_args.args[0][-2:], ["--lora", str(adapter.resolve())])
                adapter.unlink()
                self.assertFalse(local_chat_service.local_chat_pilot_available())

    def test_cli_rejects_cutoff_and_uses_instruct_checkpoint_prompt(self):
        with TemporaryDirectory() as directory:
            model = Path(directory) / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
            cli = Path(directory) / "llama-completion.exe"
            settings = local_chat_service.LocalChatSettings(str(model), cli_path=str(cli), seed=41)

            def run(args, **kwargs):
                prompt = Path(args[args.index("-f") + 1]).read_text(encoding="utf-8")
                self.assertTrue(prompt.endswith("<|im_start|>assistant\n"))
                self.assertNotIn("/no_think", prompt)
                self.assertEqual(args[-2:], ["--seed", "41"])
                return SimpleNamespace(returncode=0, stdout="Start by comparing the first")

            with patch.object(local_chat_service.subprocess, "run", side_effect=run):
                with self.assertRaisesRegex(local_chat_service.LocalChatError, "finish"):
                    local_chat_service._ask_local_cli(settings, "What should I do?", {})


class LocalChatProviderTests(unittest.TestCase):
    def test_local_mode_and_failure_have_no_external_model_calls(self):
        with patch.object(chatbot_service, "CHATBOT_PROVIDER", "local"), \
             patch.object(chatbot_service, "client") as remote, \
             patch.object(chatbot_service, "OPENROUTER_API_KEY", "synthetic-key"), \
             patch.object(chatbot_service, "ask_local_chatbot") as local:
            local.return_value = "Review your course prerequisites."
            reply = chatbot_service.ask_career_chatbot("Hello", "{}")
            self.assertEqual(reply, "Review your course prerequisites.")
            self.assertEqual(reply.mode, "local_llm")
            local.side_effect = OSError("private-runtime-failure")
            reply = chatbot_service.ask_career_chatbot("Mujhe konsi skill seekhni chahiye?", "{}")
            self.assertEqual(reply.mode, "knowledge_fallback")
            self.assertIn("dastiyab nahi", reply)
            self.assertNotIn("private-runtime-failure", reply)
            remote.chat.completions.create.assert_not_called()

    def test_live_evidence_is_preserved_in_existing_context_format(self):
        source = {"checked_at": "2026-11-27", "items": [{"title": "Sample guide"}]}
        context = json.loads(chatbot_service.build_chatbot_context(user=None, live_evidence=source))
        self.assertEqual(context["live_evidence"], source)
