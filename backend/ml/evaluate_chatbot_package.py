"""Verify packaged GGUF inference with the actual chatbot prompt and output guard."""

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import file_digest
import json
import os
from pathlib import Path
import resource
from statistics import median
from time import perf_counter

from app.services.local_chat_service import LocalChatError, LocalChatSettings, _ask_local_cli
from ml.train_chatbot import DEFAULT_DATASET, load_chat_dataset


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def student_packet(message):
    packet, _ = json.JSONDecoder().raw_decode(message["content"])
    return packet["student_question"], packet["context"]


def run_holdout(settings, cases, label):
    observations = []
    for case in cases:
        question, context = student_packet(case["messages"][-2])
        prior = case["messages"][1:-2]
        context = {
            **context,
            "recent_chat": [
                {"question": student_packet(user)[0], "response": assistant["content"]}
                for user, assistant in zip(prior[::2], prior[1::2], strict=True)
            ],
        }
        started = perf_counter()
        try:
            reply = _ask_local_cli(settings, question, context)
            outcome = {"status": "generated", "reply": reply}
        except LocalChatError as error:
            outcome = {"status": "rejected", "reason": str(error)}
        observations.append({
            "scenario_id": case["scenario_id"], "question": question,
            "reference": case["messages"][-1]["content"], "seconds": round(perf_counter() - started, 4),
            **outcome,
        })
    counts = Counter(case["status"] for case in observations)
    print(f"{label} runtime outcomes: {dict(counts)}", flush=True)
    return {
        "outcome_counts": dict(counts),
        "median_seconds": round(median(case["seconds"] for case in observations), 4),
        "observations": observations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("model", "cli", "adapter", "training-report", "out"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    args = parser.parse_args()
    training = json.loads(args.training_report.read_text(encoding="utf-8"))
    dataset_sha256 = digest(DEFAULT_DATASET)
    if training["dataset_sha256"] != dataset_sha256:
        parser.exit(1, "The adapter was trained with a different dataset version.\n")
    settings = LocalChatSettings(
        model_path=str(args.model.resolve(strict=True)), cli_path=str(args.cli.resolve(strict=True)),
        context_tokens=1024, max_tokens=96, threads=1, timeout_seconds=35,
    )
    cases = load_chat_dataset(DEFAULT_DATASET)["test"]
    baseline = run_holdout(settings, cases, "Stock model")
    trained = run_holdout(
        replace(settings, lora_path=str(args.adapter.resolve(strict=True))), cases, "Trained adapter",
    )
    manifest = {
        "base_file": args.model.name, "base_sha256": digest(args.model), "base_url": os.getenv("MODEL_URL"),
        "base_model": training["base_model"], "training_base_revision": training["base_revision"],
        "adapter_file": args.adapter.name, "adapter_sha256": digest(args.adapter),
        "runtime_tag": os.getenv("LLAMA_TAG"), "runtime_archive_sha256": os.getenv("LLAMA_SHA256"),
        "training_run": os.getenv("PACKAGE_TRAINING_RUN"), "dataset_sha256": dataset_sha256,
        "application_commit": os.getenv("GITHUB_SHA"),
        "test_cases": len(cases),
    }
    report = {
        "context_tokens": settings.context_tokens, "max_tokens": settings.max_tokens,
        "threads": settings.threads, "timeout_seconds": settings.timeout_seconds,
        "peak_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "baseline": baseline, "adapted": trained,
        "review_note": "Generated counts mean the app output guard accepted text. Human advice quality is unscored.",
    }
    for name, payload in (("manifest", manifest), ("native-holdout", report), ("training-evaluation", training)):
        (args.out / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
