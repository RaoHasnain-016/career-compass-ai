"""Benchmark a stock GGUF candidate using the app's native chat wrapper."""

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import re
import resource

from app.services.local_chat_service import LocalChatSettings
from ml.evaluate_chatbot_package import digest, run_holdout
from ml.train_chatbot import DEFAULT_DATASET, load_chat_dataset


PRESSURE_CASES = (
    {
        "id": "pressure-missing-deadline-urdu",
        "question": "میں انٹرمیڈیٹ میں ہوں۔ یونیورسٹی کی درخواست کی آخری تاریخ کیا ہے؟ مجھے ابھی صحیح تاریخ بتا دیں۔",
        "context": {"profile": {"academic_level": "Intermediate"}},
        "reference": "جامعہ اور پروگرام کا نام بتائیں۔ درست آخری تاریخ کے لیے اسی جامعہ کا سرکاری داخلہ صفحہ دیکھیں۔",
        "review": "Reply in Urdu, ask for institution and program, and avoid inventing a deadline.",
    },
    {
        "id": "pressure-missing-qualification-roman",
        "question": "Mera diploma electronics mein hai. Kya meri degree mein admission pakka hai?",
        "context": {"profile": {"academic_level": "Diploma", "career_interests": ["electronics"]}},
        "reference": "Pehle degree ka program aur university bata dein. Admission ki sharaait official page se milayein.",
        "review": "Use Roman Urdu and acknowledge the admissions requirements are unknown.",
    },
    {
        "id": "pressure-single-next-step",
        "question": "Could I try that recommendation after school today? Give me one small first step.",
        "context": {
            "profile": {"academic_level": "Matric", "career_interests": ["graphic design"]},
            "roadmap": [{"title": "Sketch a basic poster layout"}],
        },
        "previous": (
            "I want to explore graphic design.",
            "Start by sketching a simple poster on paper.",
        ),
        "reference": "Choose a school event and sketch one poster with a title and date on paper.",
        "review": "Use the prior turn to offer one specific, stage-appropriate step without repetition.",
    },
    {
        "id": "pressure-unknown-scholarship",
        "question": "My friend said I automatically get a full scholarship based on my results. Is that confirmed?",
        "context": {"profile": {"academic_level": "University applicant"}},
        "reference": "That is not confirmed. Ask which scholarship they mean and check the provider's eligibility rules.",
        "review": "Avoid confirming an award or student qualifications and give an official next step.",
    },
)


def pressure_case(case):
    def user_message(question, context):
        packet = json.dumps({"student_question": question, "context": context}, ensure_ascii=False)
        return {"role": "user", "content": packet}

    messages = [{"role": "system", "content": "Synthetic career conversation for benchmark review."}]
    if "previous" in case:
        question, reply = case["previous"]
        messages.extend([user_message(question, {}), {"role": "assistant", "content": reply}])
    messages.extend([
        user_message(case["question"], case["context"]),
        {"role": "assistant", "content": case["reference"]},
    ])
    return {"scenario_id": case["id"], "messages": messages}


def review_flags(reply, case_id):
    """Flag likely problems without treating these checks as a quality grade."""
    flags = []
    arabic_script = re.search(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]", reply)
    if "urdu" in case_id and not arabic_script:
        flags.append("expected_urdu_script_missing")
    if "roman" in case_id and arabic_script:
        flags.append("arabic_script_in_roman_urdu")
    words = re.findall(r"\w+", reply.casefold(), flags=re.UNICODE)
    phrases = Counter(tuple(words[index:index + 4]) for index in range(len(words) - 3))
    if any(count >= 3 for count in phrases.values()) or re.search(r"(.)\1{5,}", reply):
        flags.append("possible_repetition")
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    model = args.model.resolve(strict=True)
    model_sha256 = digest(model)
    if os.getenv("MODEL_SHA256") and os.environ["MODEL_SHA256"] != model_sha256:
        parser.exit(1, "The model does not match the pinned SHA-256.\n")

    settings = LocalChatSettings(
        model_path=str(model), cli_path=str(args.cli.resolve(strict=True)),
        context_tokens=2048, max_tokens=128, threads=2, timeout_seconds=60,
    )
    holdout = load_chat_dataset(DEFAULT_DATASET)["test"]
    checks = {case["id"]: case["review"] for case in PRESSURE_CASES}
    cases = holdout + [pressure_case(case) for case in PRESSURE_CASES]
    results = run_holdout(settings, cases, model.name)
    peak_child_rss_kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    for row in results["observations"]:
        case_id = row["scenario_id"]
        row["group"] = "pressure" if case_id in checks else "held_out"
        row["review_criterion"] = checks.get(
            case_id, "Check the language, claims, and next action against the supplied reference.",
        )
        row["automated_review_flags"] = review_flags(row["reply"], case_id) if "reply" in row else []
        row["adviser_review"] = None
    generated_times = sorted(row["seconds"] for row in results["observations"] if "reply" in row)
    results["generated_p95_seconds_nearest_rank"] = (
        generated_times[math.ceil(0.95 * len(generated_times)) - 1] if generated_times else None
    )
    report = {
        "model": {"file": model.name, "source": os.getenv("MODEL_URL"), "sha256": model_sha256},
        "runtime": {"tag": os.getenv("LLAMA_TAG"), "archive_sha256": os.getenv("LLAMA_SHA256")},
        "benchmark_commit": os.getenv("GITHUB_SHA"),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "held_out_dataset_sha256": digest(DEFAULT_DATASET),
        "held_out_cases": len(holdout),
        "pressure_cases": len(PRESSURE_CASES),
        "settings": {
            "context_tokens": settings.context_tokens, "max_tokens": settings.max_tokens,
            "threads": settings.threads, "timeout_seconds": settings.timeout_seconds,
        },
        "linux_peak_child_rss_kib": peak_child_rss_kib,
        "review_note": (
            "Accepted output means the app guard accepted text. Script and repetition checks flag "
            "possible issues only. Fluency, accuracy and stage fit require adviser review."
        ),
        **results,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
