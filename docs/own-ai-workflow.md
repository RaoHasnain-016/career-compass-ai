# Train and run Career Compass AI's models

Career Compass AI separates learned career ranking, language generation, and knowledge retrieval. The ranker learns which candidate careers should come first. The existing education rules provide the stage, eligibility guidance, and skills gap. A local GGUF language model uses the student's saved guidance to answer questions. Official feeds supply time-sensitive facts at request time when enabled.

## 1. Prepare the dataset

Start with `backend/ml/data/pilot_profiles.json` and its annotation guide. The pilot contains 44 synthetic profiles in 22 groups and 222 explicit judgments covering the 19 seeded careers. Its labels are synthetic. Ask an educator or adviser to independently review candidate careers on a 0–3 scale and save a separate, versioned dataset. Use anonymous IDs, keep similar profiles together, and record which examples are synthetic or reviewed.

## 2. Train and compare locally

From the project root in PowerShell:

```powershell
cd backend
$rankerPath = "ml/artifacts/career-ranker-v2"
if (-not (Test-Path $rankerPath)) { .\venv\Scripts\python.exe -m ml.train_career_ranker --out $rankerPath }
Get-Content (Join-Path $rankerPath evaluation.json)
```

The default pairwise ranker requires no ML packages. It fits on training groups, chooses regularization on validation groups, then compares itself with the rule baseline on held-out groups. Results measure agreement with the dataset judgments. In the FYP, show NDCG@3, Recall@3, the size and source of the test set, and stage-specific failure examples. For retraining, add `--dataset` and a new `--out` directory. Keep the current rules available until an independently reviewed evaluation supports switching.

The second pilot run used 28 training profiles, 8 validation profiles and 8 held-out profiles. On the judged careers, the rules reached NDCG@3 of 0.915 and Recall@3 of 0.896. The linear ranker with its eligibility safeguard reached 0.850 and 0.833. The guarded LightGBM ranker reached 0.850 and 0.896. These are synthetic comparison results. The existing rules remain the default.

## 3. Download and prove local chat inference

Run from `backend`. Download the official Qwen GGUF once and verify it before loading it:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-local-llm.txt
New-Item -ItemType Directory -Force .local-models | Out-Null
curl.exe -fL -C - -o .local-models/Qwen3-4B-Q4_K_M.gguf.part https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/a9a60d0/Qwen3-4B-Q4_K_M.gguf
if ($LASTEXITCODE -ne 0) { throw "Download incomplete. Re-run the curl command to resume." }
$modelPart = ".local-models/Qwen3-4B-Q4_K_M.gguf.part"
if ((Get-FileHash $modelPart -Algorithm SHA256).Hash -ne "7485FE6F11AF29433BC51CAB58009521F205840F5B4AE3A32FA7F92E8534FDF5") { throw "Model hash mismatch." }
Move-Item $modelPart .local-models/Qwen3-4B-Q4_K_M.gguf
.\venv\Scripts\python.exe -m ml.smoke_local_chat --model .local-models/Qwen3-4B-Q4_K_M.gguf
```

The smoke command generates answers with a synthetic student profile and blocks Python DNS and socket connections during inference. It reports the response mode and elapsed time and fails if the provider used a fallback. Repeat with stage, language, and known-answer prompts to evaluate response quality. A single smoke run does not establish quality or concurrency.

If the Windows Python wheel hits `0xc000001d` during native initialization, extract the official llama.cpp Windows CPU ZIP and keep its sibling DLLs. Set `LOCAL_CHAT_CLI_PATH` to the full path of `llama-completion.exe`, then run the same smoke command. In this compatibility mode the backend runs the executable with `--offline` and removes its private temporary prompt files after each call. A compatible in-process runtime avoids reloading the model for every response. [Official llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases)

The local Windows check used the portable b12814 runtime and a 135-million-parameter SmolLM2 test checkpoint. It generated text offline, but sometimes repeated the prompt or gave an overly generic answer. The test verifies the runtime path only. The full Qwen3 download timed out and its response quality and memory use still need testing.

## 4. Enable the models for a local or staging site

Set these variables in the backend process environment before startup, with a test database and test authentication configuration.

```powershell
$env:CAREER_RANKER_DIR = (Resolve-Path ml/artifacts/career-ranker-v2).Path
$env:CHATBOT_PROVIDER = "local"
$env:LOCAL_CHAT_MODEL_PATH = (Resolve-Path .local-models/Qwen3-4B-Q4_K_M.gguf).Path
$env:CHATBOT_LIVE_KNOWLEDGE = "1"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend runs the local model without OpenRouter. Its answer modes distinguish local LLM generation, an official-source lookup, and saved guidance when inference is unavailable. With `CHATBOT_LIVE_KNOWLEDGE=1`, admissions, university and news questions use the existing country- and stage-filtered feeds or official guides, regardless of the configured language provider. The reply links to its sources and carries the last checked time. Fetches are cached and coverage depends on publisher availability. Set `CHATBOT_LIVE_KNOWLEDGE=0` to disable those chat lookups. Local inference can still use the student's saved career and roadmap context. Firebase and other online site features have separate network dependencies.

The chat's suggested career, skill-gap, roadmap, resource and video questions use Career Compass records directly. Those replies carry the **Career Compass guidance** label and require no model API call. The student can use the same selected career across the roadmap, learning resources and career news.

## 5. Improve the models with reviewed evidence

Keep verified source updates separate from training. Add corrections and adviser-reviewed relevance labels to a new dataset version, retrain offline, compare on held-out profiles, and version the model artifact. The model does not treat student messages as training data or update its weights automatically. A future LoRA adapter can improve language or response style after you curate and evaluate a separate career Q&A dataset.

### Run the conversational training pilot

`backend/ml/data/chatbot_pilot.jsonl` contains synthetic English, Urdu and Roman Urdu conversations. Scenario IDs stay within one split. The trainer uses the user's question, synthetic profile context and earlier turns to predict the current assistant reply. Its loss only counts that reply. Download the Transformers checkpoint separately from the GGUF runtime file, and install the training packages in a dedicated environment.

Run these commands from `backend`.

```powershell
python -B -m ml.train_chatbot --validate-only
python -m venv .llm-tools/chat-training-venv
$chatPython = ".\.llm-tools\chat-training-venv\Scripts\python.exe"
& $chatPython -m pip install -r ml/requirements-chat-training.txt
& $chatPython -B -m ml.train_chatbot --model HuggingFaceTB/SmolLM2-135M-Instruct --revision 12fd25f77366fa6b3b4b768ec3050bf629380bac --out ml/artifacts/chatbot-adapter-v1 --device cpu
```

Use `--max-steps 4` for a short training smoke test. The adapter and its evaluation report are written together to a new directory. The adapter runs with the exact base checkpoint recorded in its metadata. For an offline run, point `--model` at a local copy and add `--local-files-only`. The trainer can also dequantize the existing SmolLM2 GGUF file using `--gguf` and the matching local config and tokenizer. Record the GGUF digest with `--gguf-sha256` and add `--dequantize-gguf` to the evaluation command to compare outputs against those same dequantized weights.

```powershell
& $chatPython -B -m ml.evaluate_chatbot --model .local-models/smollm2-135m-instruct-sft --adapter ml/artifacts/chatbot-adapter-v1 --out ml/artifacts/chatbot-holdout-v1.json
```

The comparison records replies and latency from the same held-out prompts. Review fluency, relevance, language, education-stage fit and unsupported facts before promoting a candidate. Token loss measures how closely the model fits the reference replies. This small pilot is intended to verify the training workflow, with a stronger multilingual model and adviser-reviewed data required for a student-facing quality evaluation.

## 6. Stage on AWS after evaluation

Version the ranker artifact, metadata and evaluation report together. Keep the GGUF and ranker artifacts in private storage. Use the existing Sydney app release flow and configure absolute local artifact paths in the backend environment. In Recommendations, choose **Preview Trained Ranking** from the sort menu to compare the pilot order with the default rule order. The preview uses existing recommendations and preserves their rule match scores. The ranker can be deployed independently of the chatbot.

The current EC2 host previously reported about 909 MiB of physical RAM. The Qwen3 4B quantized file alone is about 2.5 GB. Benchmark memory, warm and cold chat latency, and concurrent traffic on staging before selecting or paying for a larger Sydney host. Verify stage guidance, sources, login, and recovery behavior before switching the public site.

References: [Qwen3 official GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF/blob/main/Qwen3-4B-Q4_K_M.gguf), [Python inference runtime](https://github.com/abetlen/llama-cpp-python), [LightGBM ranking](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.LGBMRanker.html), [AWS EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html).
