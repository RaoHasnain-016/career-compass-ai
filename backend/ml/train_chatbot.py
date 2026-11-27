"""Fine-tune a local Career Compass chatbot adapter from reviewed conversations."""

import argparse
from collections import Counter
from dataclasses import dataclass
from hashlib import file_digest, sha256
from itertools import islice
import json
import math
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory


SPLITS = ("train", "validation", "test")
DEFAULT_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"
DEFAULT_DATASET = Path(__file__).with_name("data") / "chatbot_pilot.jsonl"
MASKED_TOKEN = -100


def load_chat_dataset(path):
    """Validate ordered messages and prevent scenarios crossing dataset splits."""
    splits = {split: [] for split in SPLITS}
    scenarios = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            split = record["split"]
            scenario = record["scenario_id"]
            messages = record["messages"]
            if split not in SPLITS or not isinstance(scenario, str) or not scenario.strip():
                raise ValueError("A known split and a nonempty scenario_id are required.")
            if scenarios.setdefault(scenario, split) != split:
                raise ValueError(f"Scenario {scenario!r} appears in more than one split.")
            if not isinstance(messages, list) or len(messages) < 2:
                raise ValueError("A conversation needs at least one question and answer.")
            if any(not isinstance(msg["content"], str) or not msg["content"].strip() for msg in messages):
                raise ValueError("Every message must contain nonempty text.")
            roles = [msg["role"] for msg in messages]
            conversational = roles[1:] if roles[0] == "system" else roles
            if not conversational or conversational != ["user", "assistant"] * (len(conversational) // 2):
                raise ValueError("A conversation must alternate user and assistant and end with an assistant reply.")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path.name} line {line_number}: {error}") from error
        splits[split].append(record)
    if not all(splits.values()):
        raise ValueError("The dataset needs nonempty train, validation and test splits.")
    return splits


def describe_splits(splits):
    return {
        split: {
            "conversations": len(records),
            "scenarios": len({record["scenario_id"] for record in records}),
            "assistant_turns": sum(
                msg["role"] == "assistant" for record in records for msg in record["messages"]
            ),
        }
        for split, records in splits.items()
    }


@dataclass
class AssistantTurn:
    token_ids: list[int]
    labels: list[int]
    truncated: bool


def tokenize_turns(tokenizer, records, max_length):
    examples = []
    for record in records:
        messages = record["messages"]
        for turn, msg in enumerate(messages):
            if msg["role"] != "assistant":
                continue
            render = {"tokenize": False, "enable_thinking": False}
            prompt = tokenizer.apply_chat_template(messages[:turn], add_generation_prompt=True, **render)
            complete = tokenizer.apply_chat_template(messages[:turn + 1], add_generation_prompt=False, **render)
            if not complete.startswith(prompt):
                raise ValueError(f"Chat template separates the reply unexpectedly in scenario {record['scenario_id']!r}.")
            encoded = tokenizer(complete, add_special_tokens=False, return_offsets_mapping=True)
            token_ids = encoded["input_ids"]
            # The prompt and every earlier assistant turn are context only for
            # this example. Preserve the current reply's end-of-turn token.
            labels = [
                token if start >= len(prompt) and end > start else MASKED_TOKEN
                for token, (start, end) in zip(token_ids, encoded["offset_mapping"], strict=True)
            ]
            target_tokens = len(labels) - labels.count(MASKED_TOKEN)
            if not 0 < target_tokens < max_length:
                raise ValueError(f"Reply in scenario {record['scenario_id']!r} needs a larger --max-length.")
            examples.append(AssistantTurn(token_ids[-max_length:], labels[-max_length:], len(token_ids) > max_length))
    return examples


def calculate_loss(model, examples, device, torch):
    model.eval()
    counts = Counter()
    with torch.inference_mode():
        for example in examples:
            loss = turn_loss(model, example, device, torch).item()
            tokens = len(example.labels) - example.labels.count(MASKED_TOKEN)
            counts["weighted_loss"] += loss * tokens
            counts["tokens"] += tokens
    return {
        "mean_assistant_token_loss": round(counts["weighted_loss"] / counts["tokens"], 6),
        "assistant_tokens": counts["tokens"],
        "turns": len(examples),
    }


def turn_loss(model, turn, device, torch):
    input_ids = torch.tensor([turn.token_ids], dtype=torch.long, device=device)
    labels = torch.tensor([turn.labels], dtype=torch.long, device=device)
    return model(input_ids=input_ids, labels=labels, use_cache=False).loss


def training_rows(examples, epochs, seed):
    random = Random(seed)
    for _ in range(epochs):
        sequence = list(examples)
        random.shuffle(sequence)
        yield from sequence


def load_gguf_checkpoint(transformers, model_directory, gguf_path, expected_sha256=None):
    """Dequantize a local GGUF with the corresponding Transformers configuration."""
    directory = Path(model_directory).resolve()
    gguf_path = Path(gguf_path).resolve()
    if not (directory / "config.json").is_file():
        raise ValueError("--gguf requires --model to be a local directory with the matching config.json and tokenizer.")
    if not gguf_path.is_file() or gguf_path.suffix.casefold() != ".gguf":
        raise ValueError("--gguf must be a local GGUF file.")
    with gguf_path.open("rb") as checkpoint:
        if checkpoint.read(4) != b"GGUF":
            raise ValueError("The selected file does not have a GGUF header.")
        checkpoint.seek(0)
        digest = file_digest(checkpoint, "sha256").hexdigest()
    if expected_sha256 and digest != expected_sha256.casefold():
        raise ValueError("GGUF SHA-256 does not match the expected checksum.")
    options = {"local_files_only": True, "trust_remote_code": False}
    config = transformers.AutoConfig.from_pretrained(str(directory), **options)
    model, loading_info = transformers.AutoModelForCausalLM.from_pretrained(
        str(directory), config=config, gguf_file=str(gguf_path),
        dtype="float32", output_loading_info=True, **options,
    )
    if any(loading_info.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")):
        raise ValueError("GGUF tensors did not fully match the local model configuration.")
    return model, {
        "format": "gguf_dequantized",
        "file": gguf_path.name,
        "sha256": digest,
        "config_sha256": sha256((directory / "config.json").read_bytes()).hexdigest(),
        "note": "Reuse this exact GGUF and config for comparable evaluation. Training loads dequantized FP32 weights.",
    }


def train_adapter(args, splits):
    import peft
    import torch
    import transformers

    if args.out.exists():
        raise ValueError(f"Output already exists: {args.out}. Choose a new output directory.")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable. Use --device cpu or configure a CUDA PyTorch build.")
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    model_id = str(args.model)
    loader_options = {
        "revision": args.revision,
        "local_files_only": args.local_files_only or args.gguf is not None,
        "trust_remote_code": False,
    }
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, use_fast=True, **loader_options)
    if not tokenizer.is_fast or not tokenizer.chat_template:
        raise ValueError("The model needs a fast tokenizer with a chat template.")
    encoded = {
        split: tokenize_turns(tokenizer, records, args.max_length) for split, records in splits.items()
    }
    if args.gguf:
        model, checkpoint = load_gguf_checkpoint(transformers, model_id, args.gguf, args.gguf_sha256)
    else:
        model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id, use_safetensors=True, **loader_options,
        )
        checkpoint = {"format": "safetensors"}
    model.to(args.device)
    model_id_for_adapter = args.base_model_id or model_id
    resolved_revision = getattr(model.config, "_commit_hash", None) or args.revision
    eval_splits = ("validation", "test")
    baseline = {split: calculate_loss(model, encoded[split], args.device, torch) for split in eval_splits}
    print("Baseline validation/test loss measured.", flush=True)
    adapter = peft.get_peft_model(model, peft.LoraConfig(
        task_type=peft.TaskType.CAUSAL_LM, r=8, lora_alpha=16, lora_dropout=0.0,
        target_modules=["q_proj", "v_proj"],
    ))
    adapter.peft_config["default"].base_model_name_or_path = model_id_for_adapter
    adapter.peft_config["default"].revision = resolved_revision
    parameters = [param for param in adapter.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=args.learning_rate)
    steps = []
    adapter.train()
    rows = training_rows(encoded["train"], args.epochs, args.seed)
    if args.max_steps is not None:
        rows = islice(rows, args.max_steps)
    for step, example in enumerate(rows, start=1):
        optimizer.zero_grad(set_to_none=True)
        loss = turn_loss(adapter, example, args.device, torch)
        value = loss.item()
        if not math.isfinite(value):
            raise ValueError(f"Nonfinite training loss at step {step}.")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
        optimizer.step()
        steps.append(round(value, 6))
        if step == 1 or step % 10 == 0:
            print(f"Step {step}, assistant-token loss {value:.3f}", flush=True)

    result = {
        "base_model": model_id_for_adapter,
        "base_revision": resolved_revision,
        "checkpoint": checkpoint,
        "dataset_sha256": sha256(args.dataset.read_bytes()).hexdigest(),
        "dataset": describe_splits(splits),
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__},
        "training": {
            "device": args.device,
            "seed": args.seed,
            "epochs_limit": args.epochs,
            "step_limit": args.max_steps,
            "steps_completed": len(steps),
            "max_length": args.max_length,
            "learning_rate": args.learning_rate,
            "trainable_parameters": sum(param.numel() for param in parameters),
            "truncated_turns": {split: sum(turn.truncated for turn in rows) for split, rows in encoded.items()},
            "step_losses": steps,
        },
        "baseline": baseline,
        "adapted": {split: calculate_loss(adapter, encoded[split], args.device, torch) for split in eval_splits},
        "metric_note": "Held-out token loss measures fit to reference replies. Assess naturalness and correctness with generated answers.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.out.parent, prefix=".adapter-training-") as temporary:
        completed = Path(temporary) / "adapter"
        adapter.save_pretrained(completed, safe_serialization=True, save_embedding_layers=False)
        tokenizer.save_pretrained(completed)
        (completed / "evaluation.json").write_text(
            json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8",
        )
        completed.rename(args.out)
    return result


def positive_int(value):
    converted = int(value)
    if converted < 1:
        raise argparse.ArgumentTypeError("Expected a positive integer.")
    return converted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--validate-only", action="store_true", help="Check the dataset without importing ML dependencies.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Transformers checkpoint directory or Hugging Face model ID.")
    parser.add_argument("--gguf", type=Path, help="Optional local GGUF weights. Use --model for the matching local config and tokenizer.")
    parser.add_argument("--gguf-sha256", help="Expected checksum for --gguf.")
    parser.add_argument("--base-model-id", help="Upstream model ID to record for a verified local checkpoint.")
    parser.add_argument("--revision", help="Checkpoint revision to pin in the adapter metadata.")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--out", type=Path, help="New directory to save adapter and evaluation.")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--epochs", type=positive_int, default=1)
    parser.add_argument("--max-steps", type=positive_int, help="Cap optimizer steps for a short pilot run.")
    parser.add_argument("--max-length", type=positive_int, default=512)
    parser.add_argument("--threads", type=positive_int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    try:
        splits = load_chat_dataset(args.dataset)
        if args.validate_only:
            result = describe_splits(splits)
        else:
            if args.out is None:
                parser.error("--out is required for training")
            if args.gguf and not (Path(args.model) / "config.json").is_file():
                parser.error("--gguf requires a matching local --model configuration and tokenizer directory")
            if args.gguf_sha256 and not args.gguf:
                parser.error("--gguf-sha256 requires --gguf")
            if not 0 < args.learning_rate < 1:
                parser.error("--learning-rate must be between zero and one")
            result = train_adapter(args, splits)
    except (OSError, ValueError, ImportError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
