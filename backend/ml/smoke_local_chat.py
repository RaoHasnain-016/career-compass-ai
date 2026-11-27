"""Exercise the local chatbot engine with a synthetic profile and no network."""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path, help="Local GGUF file")
    parser.add_argument("--question", action="append", help="Repeat to run multiple warm checks")
    args = parser.parse_args()

    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["CHATBOT_PROVIDER"] = "local"
    os.environ["LOCAL_CHAT_MODEL_PATH"] = str(args.model.resolve())
    from app.services.chatbot_service import ask_career_chatbot

    context = json.dumps({
        "profile": {"academic_level": "Matric", "country": "Pakistan", "interests": ["computing"]},
        "selected_career": {"title": "Software Engineer", "required_education": "Start with suitable Intermediate subjects before degree study."},
        "roadmap": [{"stage_order": 1, "title": "Compare ICS and Pre-Engineering", "description": "Ask your school about subject requirements."}],
    })
    questions = args.question or ["What is my next study step after Matric if I like computing?"]
    all_local = True
    with patch("socket.socket.connect", side_effect=AssertionError("Offline smoke test forbids network connections")), \
            patch("socket.getaddrinfo", side_effect=AssertionError("Offline smoke test forbids DNS lookup")):
        for question in questions:
            started = perf_counter()
            answer = ask_career_chatbot(question, context)
            mode = getattr(answer, "mode", "unknown")
            all_local &= mode == "local_llm"
            print(json.dumps({
                "question": question,
                "mode": mode,
                "seconds": round(perf_counter() - started, 2),
                "answer": str(answer),
            }, ensure_ascii=True))
    if not all_local:
        raise SystemExit("At least one question used fallback. Check the model file and runtime before release.")


if __name__ == "__main__":
    main()
