import json
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from ml.train_chatbot import MASKED_TOKEN, load_chat_dataset, load_gguf_checkpoint, tokenize_turns


class CharacterTokenizer:
    def apply_chat_template(self, messages, *, tokenize, enable_thinking, add_generation_prompt):
        text = "".join(f"{message['role']}: {message['content']}\n" for message in messages)
        return text + ("assistant: " if add_generation_prompt else "")

    def __call__(self, text, *, add_special_tokens, return_offsets_mapping):
        return {
            "input_ids": [ord(character) for character in text],
            "offset_mapping": [(index, index + 1) for index in range(len(text))],
        }


class ChatbotTrainingTests(unittest.TestCase):
    def test_only_current_assistant_reply_is_supervised(self):
        record = {
            "scenario_id": "multi-turn",
            "messages": [
                {"role": "system", "content": "Use the supplied facts."},
                {"role": "user", "content": "How should I start?"},
                {"role": "assistant", "content": "Which subjects do you enjoy?"},
                {"role": "user", "content": "Mathematics."},
                {"role": "assistant", "content": "Start with a small coding project."},
            ],
        }
        first, second = tokenize_turns(CharacterTokenizer(), [record], max_length=100)
        expected = ["Which subjects do you enjoy?\n", "Start with a small coding project.\n"]
        self.assertEqual([
            "".join(chr(value) for value in example.labels if value != MASKED_TOKEN)
            for example in (first, second)
        ], expected)
        self.assertTrue(second.truncated)
        self.assertEqual(second.labels[0], MASKED_TOKEN)

    def test_same_scenario_in_different_splits_is_rejected(self):
        messages = [{"role": "user", "content": "Question"}, {"role": "assistant", "content": "Answer"}]
        rows = [
            {"scenario_id": "shared", "split": split, "messages": messages}
            for split in ("train", "validation", "test")
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "conversations.jsonl"
            path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "appears in more than one split"):
                load_chat_dataset(path)

    def test_gguf_loader_verifies_the_checkpoint_and_uses_local_configuration(self):
        with TemporaryDirectory() as directory:
            model_directory = Path(directory)
            config = model_directory / "config.json"
            config.write_bytes(b'{"model_type":"llama"}')
            weights = model_directory / "model.gguf"
            weights.write_bytes(b"GGUF synthetic checkpoint bytes")
            expected = sha256(weights.read_bytes()).hexdigest()
            transformers = Mock()
            model = object()
            transformers.AutoModelForCausalLM.from_pretrained.return_value = (model, {})
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_gguf_checkpoint(transformers, model_directory, weights, "0" * 64)
            transformers.AutoConfig.from_pretrained.assert_not_called()
            loaded, provenance = load_gguf_checkpoint(transformers, model_directory, weights, expected)
            self.assertIs(loaded, model)
            self.assertEqual(provenance["sha256"], expected)
            self.assertEqual(provenance["config_sha256"], sha256(config.read_bytes()).hexdigest())
            options = transformers.AutoModelForCausalLM.from_pretrained.call_args.kwargs
            self.assertTrue(options["local_files_only"])
            self.assertFalse(options["trust_remote_code"])


if __name__ == "__main__":
    unittest.main()
