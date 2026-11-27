# Adviser review for the Career Compass chatbot

Use this sheet to review actual model replies to the nine synthetic test conversations in [chatbot_pilot.jsonl](chatbot_pilot.jsonl). The expectations below describe evidence and useful next steps. Accept equivalent answers in the student's language. This sheet contains no adviser scores or real student records.

## Review the held-out conversations

1. Load each conversation's final question, supplied profile and evidence, and any preceding turns. For the pilot benchmark, use the observations in `native-holdout.json`. The [previous benchmark run](https://github.com/RaoHasnain-016/career-compass-ai/actions/runs/46053952497) contains separate base and adapter replies.
2. Give two reviewers the same replies with model names masked and the order varied. Include a reviewer fluent in Urdu script and Roman Urdu. Score independently and preserve both sets of scores before resolving disagreements.
3. Record an empty, rejected, or timed-out generation as an outcome. When testing the application, separately record whether the student actually received a usable saved-guidance fallback. Keep all cases in the denominator.

| Scenario ID | Student question or situation | What to check |
| --- | --- | --- |
| `matric-school-medical-follow-up` | “I don't know whether I like working with people or looking at samples more.” | Uses the prior hospital conversation. Compares a patient-facing role with a laboratory role and offers an exploration step a Matric student can take, such as comparing typical tasks with a teacher. |
| `matric-engineering-roman-test` | “Mujhe cheezen design karna pasand hai. Matric mein ab kis cheez se shuru karun?” | Replies in Roman Urdu. Suggests a small sketch or layout exercise and links it to choosing senior-secondary subjects. |
| `intermediate-vague-field-urdu-test` | “مجھے ابھی سمجھ نہیں آ رہی کہ آگے کیا پڑھوں۔ آپ میری کیسے مدد کریں گے؟” | Replies in Urdu script and asks a focused question about subjects or activities before narrowing the options. |
| `intermediate-stale-notice` | “Can I apply this Friday from the update in the app?” | Explains that the stale notice has no confirmed programme deadline. Asks for the institution and course and points to the official current intake before the student relies on Friday. |
| `diploma-limited-lab-access` | “I have an electrical diploma and can't get into a lab right now. How do I practise troubleshooting?” | Suggests a simulator or sample diagram and a way to record the troubleshooting steps. Respects the lack of lab access. |
| `diploma-degree-roman-test` | “Meri DAE Civil complete hai. Kya ab mujhe seedha degree mein admission mil jayega?” | Explains in Roman Urdu that eligibility depends on the programme and its current requirements. Directs the student to confirm the qualification with the institution before assuming admission. |
| `university-roads-urdu-test` | “میری روڈمیپ میں کئی کام ہیں۔ آج کون سا کام کروں تاکہ آغاز ہو جائے؟” | Replies in Urdu script. Uses the first saved roadmap step, cleaning a dataset, and proposes one concrete spreadsheet task. |
| `university-real-link-only` | “Could you link me to the Git book in my resources and tell me what to try first?” | Copies the supplied URL exactly, `https://git-scm.com/book/en/v2`, and suggests one beginner action such as making a commit in a practice repository. |
| `university-portfolio-followup` | “Will it count if I only use spreadsheets?” | Connects the reply to the student's first data portfolio. Explains how a spreadsheet can show their reasoning through formulas, charts, or a short explanation. |

## Score and record the replies

Use `3` for meets expectations, `2` for partial, and `1` for poor. Use `NA` for follow-up only when the case has no preceding exchange and needs no clarification. Leave scores blank when no reply was available and record the runtime reason.

| Dimension | What a score of 3 means |
| --- | --- |
| `naturalness` | Answers the question directly in clear, fluent language without copying it back or repeating phrases. |
| `language_fit` | Uses the expected language and script, preserving the spelling of names and URLs where appropriate. |
| `grounding` | Uses the supplied details accurately and acknowledges missing or stale evidence. |
| `stage_fit` | Gives a feasible next step at the student's current stage and treats a future career as a longer-term goal. |
| `follow_up` | Uses the relevant prior turn or asks a specific question when an important detail is missing. |

Flag confirmed advice about an unverified deadline or eligibility, an invented link or source, or an unsafe action as a critical error. For example, replying “Yes, you can apply for the job” to the stale-notice scenario is a critical grounding error even if the wording is fluent.

Use UTF-8 CSV and one row per reviewer, scenario and reply. In `issue_note`, quote the problematic phrase and name the relevant evidence. Record a brief candidate correction in `suggested_revision` for later review.

```csv
run_id,dataset_sha256,scenario_id,reply_label,reviewer_id,delivery_mode,outcome,naturalness,language_fit,grounding,stage_fit,follow_up,critical_error,issue_note,suggested_revision
```

Keep a run record alongside it with the exact model revision, its file checksum, adapter checksum if applicable, application commit, runtime settings, and hardware. Use reviewer codes in the score sheet.

## Proposed gates for a student-facing preview

- Score all nine scenarios using the effective candidate and fallback configuration. Require zero critical errors and zero unhandled failures. Check the stale notice, diploma eligibility and exact link cases explicitly.
- Require `grounding` and `stage_fit` of at least `2` in every user-visible reply and `language_fit` of `3` in every case. Require `naturalness` of `3` in at least seven of nine cases and `follow_up` of at least `2` wherever applicable.
- Compare the candidate with the previous model or saved guidance under the same prompts. Report how many cases were directly answered, routed to official sources, or handled by fallback. Report the raw counts by stage and language. A safety or language regression must be resolved and retested before release.

These gates are proposed for the small pilot. A passing count describes these nine cases only. Staging also needs separate memory, latency, and health checks using the exact files that would serve traffic.

## Add adviser-reviewed examples

Use fictional profiles and preserve a clear record of who reviewed each example and what changed. Build coverage across the four education stages and three language variants, including realistic follow-ups and cases with missing or contradictory information. Group a scenario and all its paraphrases, translations, and follow-ups together. Keep the entire group in a single split. Add revised examples to training only when their scenario groups are outside the held-out test set. Keep a versioned, frozen test set for each comparison.
