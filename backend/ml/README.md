# Career ranker training

The trainer reads the offline seed catalog and the judged pairs in `data/pilot_profiles.json`. The pilot is synthetic. Its results describe agreement with the pilot labels. Use a separate reviewed evaluation set before enabling model ranking for students.

Run inside the project's backend Python environment from the repository root.

```powershell
cd backend
python -m ml.train_career_ranker
python -m unittest tests.test_career_ranker -v
```

The default artifact directory `backend/ml/artifacts/career-ranker` contains the learned linear weights in JSON, metadata, and evaluation report. The linear trainer and loader use Python's standard library. For a subsequent run, pass `--out ml/artifacts/career-ranker-v2`. Add `--dataset <path>` for a separate dataset with the same schema.

The default model learns pairwise preferences from careers with different ratings for the same student. Training uses normalized grades, academic stage/readiness, subject and skill overlap, career interests, and study preferences. It splits entire scenario groups into training, validation, and held-out testing. The report includes NDCG@3 and Recall@3 for the rule baseline, the raw ranker, and the ranker with the eligibility constraint. Metrics cover the explicitly judged careers only. Per-profile results and split counts help identify stages and countries with limited coverage.

Optional LightGBM experiment

```powershell
python -m pip install -r ml/requirements-ranker.txt
python -m ml.train_career_ranker --algorithm lightgbm --out ml/artifacts/career-ranker-lgbm
```

This writes a native LightGBM text model and requires LightGBM on the inference host too.

On a test backend, enable learning-based ranking with `CAREER_RANKER_DIR` pointed at the artifact directory. Use an absolute path when running outside `backend`.

```powershell
$env:CAREER_RANKER_DIR = (Resolve-Path ml/artifacts/career-ranker).Path
```

Restart the backend after changing the artifact. Use **Preview Trained Ranking** in Recommendations to try the pilot. The endpoints `/recommendations/generate?ranking=model` and `/recommendations/me?ranking=model` return `ranking_source: "trained"` and `model_rank` positions when inference succeeds. Rule-derived percentages and explanations remain available. The eligibility policy keeps careers with unmet prerequisites after immediately actionable paths. A missing or incompatible model uses the rule order. After changing profile details, generate new recommendations to refresh their stored explanations and eligibility.

**Personalized Order** uses bookmarks immediately to prioritize eligible or nearly eligible paths for that student. Bookmarks stay scoped to the student and influence the ordering at request time. Training the model requires a separate reviewed and versioned dataset.

To improve the model, collect explicitly rated paths from reviewers with consent and limit records to necessary profile features and anonymous IDs. Retrain and evaluate a new artifact offline. Profile edits, the current career catalog, and official source refreshes are available at inference time. Stored feedback only affects learned weights after it has been reviewed and added to a versioned training set.
