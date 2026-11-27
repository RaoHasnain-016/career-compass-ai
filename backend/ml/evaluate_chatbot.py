"""Evaluate a local chatbot on the final user turn of held-out conversations."""

import argparse
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from statistics import median
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter

from ml.train_chatbot import DEFAULT_DATASET, load_chat_dataset


CLI_ENV_KEYS = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG", "LC_ALL"}
HUMAN_RUBRIC = {
    "scale": "1 poor, 2 partial, 3 meets expectations. Null means unreviewed.",
    "naturalness": "Responds to the latest turn in clear, conversational phrasing and the student's language.",
    "grounding": "Uses supplied profile and sources accurately. Handles unknown dates and eligibility explicitly.",
    "stage_fit": "Gives a feasible next action for the student’s current education stage.",
    "follow_up": "Accounts for the prior exchange and clarifies missing information when needed.",
}


def read_held_out(data_file):
    splits = load_chat_dataset(data_file)
    cases = [
        {
            "case": index,
            "scenario_id": row["scenario_id"],
            "prompt": row["messages"][:-1],
            "reference": row["messages"][-1]["content"],
        }
        for index, row in enumerate(splits["test"], start=1)
    ]
    return cases, {split: len(rows) for split, rows in splits.items()}, sha256(data_file.read_bytes()).hexdigest()


def transformer_generator(model, tokenizer, torch, device, max_new_tokens):
    pad_token = tokenizer.pad_token_id
    if pad_token is None:
        pad_token = tokenizer.eos_token_id

    def generate(messages):
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, enable_thinking=False,
            tokenize=True, return_dict=True, return_tensors="pt",
        ).to(device)
        prompt_length = inputs["input_ids"].shape[1]
        with torch.inference_mode():
            output = model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=False,
                pad_token_id=pad_token,
            )
        reply_tokens = output[0, prompt_length:]
        return tokenizer.decode(reply_tokens, skip_special_tokens=True), len(reply_tokens)

    return generate


def gguf_generator(args):
    def generate(messages):
        # The project uses the ChatML GGUF exports of Qwen3 and SmolLM2.
        prompt = "".join(
            f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n" for item in messages
        ) + "<|im_start|>assistant\n"
        if args.gguf.name.casefold().startswith("qwen3"):
            prompt += "<think>\n\n</think>\n\n"
        with TemporaryDirectory(prefix="career-chat-eval-") as directory:
            prompt_file = Path(directory) / "prompt.txt"
            prompt_file.write_text(prompt, encoding="utf-8")
            result = subprocess.run(
                [
                    str(args.llama_cli), "--offline", "--no-conversation", "--no-display-prompt",
                    "--color", "off", "-m", str(args.gguf), "-f", str(prompt_file),
                    "-c", "2048", "-t", str(args.threads), "-n", str(args.max_new_tokens), "--temp", "0",
                ],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=args.timeout, check=True,
                env={name: value for name, value in os.environ.items() if name.upper() in CLI_ENV_KEYS},
            )
        text = result.stdout.partition("<|im_end|>")[0].strip().removesuffix("[end of text]").strip()
        return text, None

    return generate


def last_question(messages):
    content = messages[-1]["content"].strip()
    try:
        packet, _ = json.JSONDecoder().raw_decode(content)
    except ValueError:
        return content
    if isinstance(packet, dict) and isinstance(packet.get("student_question"), str):
        return packet["student_question"].strip()
    return content


def compare_cases(results, label, generate):
    counts = Counter()
    timings = []
    for case in results:
        started = perf_counter()
        try:
            reply, token_count = generate(case["prompt"])
            reply = reply.strip()
            status = "generated" if reply else "empty"
            candidate = reply.strip("'\"").strip().casefold()
            if candidate and candidate == last_question(case["prompt"]).casefold():
                status = "exact_user_echo"
            outcome = {"reply": reply, "generated_tokens": token_count}
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
            status = "error"
            outcome = {"error_type": type(error).__name__}
        duration = perf_counter() - started
        counts[status] += 1
        if status != "error":
            timings.append(duration)
        case.setdefault("outputs", {})[label] = {
            **outcome, "status": status, "seconds": round(duration, 4),
            "human_scores": dict.fromkeys(("naturalness", "grounding", "stage_fit", "follow_up")),
        }
    return {
        "outcome_counts": dict(counts), "latency_samples": len(timings),
        "median_seconds": round(median(timings), 4) if timings else None,
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    model_group = parser.add_mutually_exclusive_group(required=True)
    model_group.add_argument("--model", type=Path, help="Local Transformers checkpoint directory")
    model_group.add_argument("--gguf", type=Path, help="Local ChatML GGUF file for a baseline check")
    parser.add_argument("--dequantize-gguf", type=Path, help="Use these local weights with the Transformers --model directory")
    parser.add_argument("--adapter", type=Path, help="Compare a local LoRA adapter against --model")
    parser.add_argument("--llama-cli", type=Path, help="Path to llama-completion for --gguf")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out", type=Path, required=True, help="New JSON report")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--limit", type=int, help="Limit the number of held-out cases for a quick check")
    parser.add_argument("--timeout", type=float, default=45.0, help="Timeout per GGUF process in seconds")
    args = parser.parse_args()
    if not 1 <= args.threads <= 16 or not 16 <= args.max_new_tokens <= 320:
        parser.error("Use 1–16 threads and 16–320 new tokens.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")
    if not 2 <= args.timeout <= 180:
        parser.error("Use a timeout from 2 to 180 seconds.")
    if args.model and (not args.model.is_dir() or args.llama_cli):
        parser.error("--model must be a local directory and cannot be combined with --llama-cli.")
    if args.dequantize_gguf and (not args.model or not args.dequantize_gguf.is_file()):
        parser.error("--dequantize-gguf requires --model and a local GGUF weights file.")
    if args.gguf and (args.adapter or args.device != "cpu" or not args.gguf.is_file()
                      or args.gguf.suffix.casefold() != ".gguf" or not args.llama_cli
                      or not args.llama_cli.is_file()
                      or args.llama_cli.name.casefold() not in {"llama-completion", "llama-completion.exe"}):
        parser.error("--gguf requires a local .gguf file and llama-completion, with CPU and no adapter.")
    if args.adapter and not (args.adapter / "adapter_model.safetensors").is_file():
        parser.error("--adapter must be a local directory with adapter_model.safetensors.")
    if args.out.exists():
        parser.error("--out already exists. Choose a new report path.")
    return args


def main():
    args = parse_args()
    try:
        cases, split_counts, digest = read_held_out(args.data)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    selected_cases = cases[:args.limit]
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "dataset": args.data.name, "dataset_sha256": digest, "split_counts": split_counts,
        "evaluation_split": "test", "cases_evaluated": len(selected_cases), "case_limit": args.limit,
        "method": "Generate only the final answer with the earlier authored turns as context. No warmup.",
        "generation": {"strategy": "greedy", "max_new_tokens": args.max_new_tokens,
                       "device": args.device, "threads": args.threads},
        "human_review": HUMAN_RUBRIC, "cases": selected_cases,
    }
    if args.gguf:
        args.gguf = args.gguf.resolve()
        args.llama_cli = args.llama_cli.resolve()
        report["engine"] = "llama.cpp subprocess"
        report["timing_scope"] = "A fresh process and model load for each answer."
        report["base_model"] = args.gguf.name
        report["base"] = compare_cases(selected_cases, "base", gguf_generator(args))
    else:
        os.environ["HF_HUB_OFFLINE"] = "1"
        try:
            import torch
            import transformers
            if args.adapter:
                from peft import PeftModel
        except ImportError as error:
            raise SystemExit("Install the optional requirements-chat-training.txt dependencies.") from error
        if args.device == "cuda" and not torch.cuda.is_available():
            raise SystemExit("CUDA is unavailable. Use --device cpu or a CUDA-enabled machine.")
        torch.set_num_threads(args.threads)
        started = perf_counter()
        model_directory = str(args.model.resolve())
        tokenizer = transformers.AutoTokenizer.from_pretrained(model_directory, local_files_only=True)
        training_report = None
        if args.adapter:
            report_path = args.adapter / "evaluation.json"
            if report_path.is_file():
                training_report = json.loads(report_path.read_text(encoding="utf-8"))
                trained_digest = training_report.get("dataset_sha256")
                report["adapter_training_dataset_sha256"] = trained_digest
                report["adapter_dataset_matches"] = trained_digest == digest
        if args.dequantize_gguf:
            from ml.train_chatbot import load_gguf_checkpoint

            checkpoint = (training_report or {}).get("checkpoint", {})
            if args.adapter and checkpoint.get("format") != "gguf_dequantized":
                raise SystemExit("The adapter training report must identify its original GGUF checkpoint.")
            model, provenance = load_gguf_checkpoint(
                transformers, args.model.resolve(), args.dequantize_gguf.resolve(),
                expected_sha256=checkpoint.get("sha256"),
            )
            if args.adapter and any(checkpoint.get(key) != provenance[key] for key in ("sha256", "config_sha256")):
                raise SystemExit("The adapter's training checkpoint differs from the requested base.")
            report["checkpoint"] = provenance
        else:
            if (training_report or {}).get("checkpoint", {}).get("format") == "gguf_dequantized":
                raise SystemExit("This adapter requires the original --dequantize-gguf weights.")
            model = transformers.AutoModelForCausalLM.from_pretrained(
                model_directory, local_files_only=True, use_safetensors=True,
            )
        model = model.to(args.device).eval()
        report["engine"] = "Transformers"
        report["timing_scope"] = "Tokenization, generation, and decoding. Model loading is recorded separately."
        report["base_model"] = args.model.name
        report["base_model_load_seconds"] = round(perf_counter() - started, 4)
        report["base"] = compare_cases(
            selected_cases, "base", transformer_generator(model, tokenizer, torch, args.device, args.max_new_tokens),
        )
        if args.adapter:
            started = perf_counter()
            model = PeftModel.from_pretrained(model, str(args.adapter.resolve()), local_files_only=True).eval()
            report["adapter"] = args.adapter.name
            report["adapter_load_seconds"] = round(perf_counter() - started, 4)
            report["adapted"] = compare_cases(
                selected_cases, "adapted", transformer_generator(model, tokenizer, torch, args.device, args.max_new_tokens),
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"Wrote {len(selected_cases)} held-out cases to {args.out}. Human scores are unreviewed.")


if __name__ == "__main__":
    main()
