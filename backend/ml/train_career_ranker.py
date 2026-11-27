"""Train a local career ranker using explicitly judged profile/career pairs."""

import argparse
import ast
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from math import exp, isfinite, log2
from pathlib import Path
from random import Random
from types import SimpleNamespace

from app.services.career_ranker import (
    FEATURE_NAMES, LINEAR_MODEL_FORMAT, MODEL_FORMAT, _LinearRanker, career_rank_features, ranking_policy_key,
)
from app.services.recommendation_service import generate_recommendation_analysis


HERE = Path(__file__).resolve().parent
DEFAULT_CATALOG = HERE.parent / "seed_data.py"
DEFAULT_DATASET = HERE / "data" / "pilot_profiles.json"
DEFAULT_OUTPUT = HERE / "artifacts" / "career-ranker"


@dataclass(frozen=True)
class JudgedCareer:
    title: str
    features: tuple
    relevance: int
    baseline: float
    eligibility: str


@dataclass(frozen=True)
class ProfileGroup:
    profile_id: str
    group_id: str
    country: str
    academic_level: str
    candidates: tuple[JudgedCareer, ...]


def load_catalog(path):
    """Read literal seed definitions without importing or running the seeder."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    seed = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "seed_careers"), None)
    if seed is None:
        raise ValueError("The seed file does not define seed_careers.")
    records = []
    for node in seed.body:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "add_career":
            records.append(ast.literal_eval(value.args[1]))
        if any(isinstance(target, ast.Name) and target.id == "additional_careers" for target in node.targets):
            records.extend(ast.literal_eval(value))
    catalog = {record["title"]: SimpleNamespace(**record) for record in records if record.get("status", True)}
    if not catalog or len(catalog) != len(records):
        raise ValueError("The offline seed catalog is empty or has duplicate/disabled records.")
    return catalog


def _profile_text(row, key, *, required=False):
    value = row.get(key, "")
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"{key} must be a valid string.")
    return value.strip()


def _profile_values(row):
    marks = row.get("marks_cgpa")
    if marks is not None and (type(marks) not in (int, float) or not isfinite(marks) or not 0 <= marks <= 100):
        raise ValueError("marks_cgpa must be null or a finite value from 0 to 100.")
    preference = _profile_text(row, "study_preference")
    for limit in (4, 5):
        if f"academic scale: gpa out of {limit}" in preference.casefold() and marks is not None and marks > limit:
            raise ValueError(f"marks_cgpa is above the stated GPA scale of {limit}.")
    profile = {
        "academic_level": _profile_text(row, "academic_level", required=True),
        "country": _profile_text(row, "country", required=True),
        "study_preference": preference,
        "marks_cgpa": marks,
    }
    for attr in ("interests", "skills", "favorite_subjects"):
        values = row.get(attr, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"{attr} must be a list of nonempty strings.")
        profile[attr] = values
    return SimpleNamespace(**profile)


def load_judgments(path, catalog):
    raw = path.read_bytes()
    dataset = json.loads(raw)
    if not isinstance(dataset, dict) or not isinstance(dataset.get("profiles"), list):
        raise ValueError("The dataset must contain a profiles array.")
    provenance = _profile_text(dataset, "label_provenance", required=True)
    metadata = {
        "dataset_id": _profile_text(dataset, "dataset_id", required=True),
        "label_provenance": provenance,
        "dataset_sha256": sha256(raw).hexdigest(),
    }
    profiles = []
    profile_ids = set()
    for row in dataset["profiles"]:
        if not isinstance(row, dict):
            raise ValueError("Every profile must be a JSON object.")
        profile_id = _profile_text(row, "profile_id", required=True)
        group_id = _profile_text(row, "group_id", required=True)
        if profile_id in profile_ids:
            raise ValueError(f"Duplicate profile_id: {profile_id}")
        profile_ids.add(profile_id)
        profile = _profile_values(row)
        labels = row["labels"]
        if not isinstance(labels, dict) or len(labels) < 4:
            raise ValueError(f"{profile_id} must have four or more judged careers.")
        if any(type(value) is not int or not 0 <= value <= 3 for value in labels.values()):
            raise ValueError(f"{profile_id} has a relevance label outside 0–3.")
        if max(labels.values()) < 2 or min(labels.values()) != 0:
            raise ValueError(f"{profile_id} needs a relevant path and at least one explicit poor fit.")
        judged = []
        for title, relevance in sorted(labels.items()):
            if title not in catalog:
                raise ValueError(f"Unknown career title in {profile_id}: {title}")
            career = catalog[title]
            baseline = generate_recommendation_analysis(profile, career)
            judged.append(JudgedCareer(title, tuple(career_rank_features(profile, career)), relevance,
                                      baseline["score"], baseline["eligibility_status"]))
        profiles.append(ProfileGroup(profile_id, group_id, profile.country, profile.academic_level, tuple(judged)))
    return profiles, metadata


def split_by_group(profiles, seed):
    groups = sorted({profile.group_id for profile in profiles})
    if len(groups) < 6:
        raise ValueError("At least six independent scenario groups are needed for train, validation, and test.")
    Random(seed).shuffle(groups)
    held_out = max(1, round(len(groups) * 0.2))
    test_ids = set(groups[:held_out])
    validation_ids = set(groups[held_out:2 * held_out])
    train_ids = set(groups[2 * held_out:])
    return [
        [profile for profile in profiles if profile.group_id in allowed]
        for allowed in (train_ids, validation_ids, test_ids)
    ]


def _profile_metrics(labels, k=3):
    def dcg(order):
        return sum((2 ** label - 1) / log2(index + 2) for index, label in enumerate(order[:k]))

    ideal = dcg(sorted(labels, reverse=True))
    relevant = sum(label >= 2 for label in labels)
    return {
        "ndcg_at_3": dcg(labels) / ideal if ideal else 0,
        "recall_at_3": sum(label >= 2 for label in labels[:k]) / relevant if relevant else 0,
    }


def _average_metrics(records):
    return {key: round(sum(item[key] for item in records) / len(records), 5) for key in records[0]}


def evaluate(profiles, predict):
    baseline_scores, trained_scores, raw_scores = [], [], []
    sample_details = []
    for profile in profiles:
        candidates = profile.candidates
        scores = [float(score) for score in predict([candidate.features for candidate in candidates])]
        if len(scores) != len(candidates) or not all(isfinite(score) for score in scores):
            raise ValueError("Model did not return a finite score for every judged career.")
        baseline_order = sorted(candidates, key=lambda candidate: (-candidate.baseline, candidate.title.casefold()))
        raw_order = sorted(zip(candidates, scores), key=lambda pair: (-pair[1], -pair[0].baseline, pair[0].title.casefold()))
        learned_order = baseline_order
        if len(set(scores)) > 1:
            learned_order = [candidate for candidate, _ in sorted(zip(candidates, scores), key=lambda pair: ranking_policy_key(
                pair[0].eligibility, pair[1], pair[0].baseline, pair[0].title,
            ))]
        baseline_scores.append(_profile_metrics([candidate.relevance for candidate in baseline_order]))
        raw_scores.append(_profile_metrics([candidate.relevance for candidate, _ in raw_order]))
        trained_scores.append(_profile_metrics([candidate.relevance for candidate in learned_order]))
        sample_details.append({
            "profile_id": profile.profile_id, "group_id": profile.group_id,
            "country": profile.country, "academic_level": profile.academic_level,
            "judged_careers": len(candidates),
            "baseline_top_3": [candidate.title for candidate in baseline_order[:3]],
            "trained_top_3": [candidate.title for candidate in learned_order[:3]],
        })
    return {
        "rule_baseline": _average_metrics(baseline_scores),
        "model_only": _average_metrics(raw_scores),
        "trained_with_eligibility_guard": _average_metrics(trained_scores),
        "per_profile": sample_details,
    }


def _make_lightgbm_dataset(profiles, lightgbm, numpy):
    candidates = [candidate for profile in profiles for candidate in profile.candidates]
    return lightgbm.Dataset(
        numpy.asarray([candidate.features for candidate in candidates], dtype="float64"),
        label=[candidate.relevance for candidate in candidates],
        group=[len(profile.candidates) for profile in profiles],
        feature_name=list(FEATURE_NAMES),
    )


def _split_summary(profiles):
    return {
        "profile_count": len(profiles),
        "group_count": len({profile.group_id for profile in profiles}),
        "pair_count": sum(len(profile.candidates) for profile in profiles),
        "stages": dict(Counter(profile.academic_level for profile in profiles)),
        "countries": dict(Counter(profile.country for profile in profiles)),
    }


def _fit_pairwise(profiles, penalty, steps=320):
    comparisons = []
    for profile in profiles:
        pairs = [
            tuple(a - b for a, b in zip(better.features, worse.features))
            for better in profile.candidates
            for worse in profile.candidates if better.relevance > worse.relevance
        ]
        comparisons.extend((difference, 1 / len(pairs)) for difference in pairs)
    if not comparisons:
        raise ValueError("Training requires a profile with at least two different relevance ratings.")

    weights = [0.0] * len(FEATURE_NAMES)
    for _ in range(steps):
        gradient = [penalty * weight for weight in weights]
        for difference, pair_weight in comparisons:
            margin = sum(weight * value for weight, value in zip(weights, difference))
            residual = pair_weight / (len(profiles) * (1 + exp(max(-40, min(40, margin)))))
            for index, value in enumerate(difference):
                gradient[index] -= residual * value
        weights = [weight - 0.3 * update for weight, update in zip(weights, gradient)]
    return _LinearRanker(weights)


def _train_lightgbm(train_profiles, validation_profiles, seed):
    import lightgbm as lgb
    import numpy as np

    train_rows = _make_lightgbm_dataset(train_profiles, lgb, np)
    validation_rows = _make_lightgbm_dataset(validation_profiles, lgb, np)
    model = lgb.train(
        {"objective": "lambdarank", "metric": "ndcg", "ndcg_at": [3], "seed": seed,
         "num_threads": 1, "deterministic": True, "force_col_wise": True,
         "max_depth": 3, "num_leaves": 7, "min_data_in_leaf": 5, "verbosity": -1},
        train_rows, num_boost_round=80, valid_sets=[validation_rows],
        callbacks=[lgb.early_stopping(12, verbose=False)],
    )
    return model, lgb.__version__, lambda rows: model.predict(np.asarray(rows, dtype="float64"), num_threads=1)


def train(dataset, catalog, output, seed, algorithm="linear"):
    if output.exists():
        raise FileExistsError(f"Pick a new artifact directory: {output}")
    catalog_records = load_catalog(catalog)
    profiles, provenance = load_judgments(dataset, catalog_records)
    train_profiles, validation_profiles, test_profiles = split_by_group(profiles, seed)
    output_model = {}
    if algorithm == "linear":
        candidates = [(_fit_pairwise(train_profiles, penalty), penalty) for penalty in (0.01, 0.07)]
        model, penalty = max(candidates, key=lambda entry: evaluate(
            validation_profiles, entry[0].predict,
        )["trained_with_eligibility_guard"]["ndcg_at_3"])
        predict = model.predict
        model_format, model_version = LINEAR_MODEL_FORMAT, "1"
        output_model["l2_penalty"] = penalty
    else:
        model, model_version, predict = _train_lightgbm(train_profiles, validation_profiles, seed)
        model_format = MODEL_FORMAT
        output_model["trained_boosting_rounds"] = model.current_iteration()
    evaluation = evaluate(test_profiles, predict)
    report = {
        **provenance, "seed": seed, "algorithm": algorithm, "model_version": model_version, **output_model,
        "catalog_sha256": sha256(catalog.read_bytes()).hexdigest(),
        "catalog_size": len(catalog_records),
        "splits": {name: _split_summary(partition) for name, partition in zip(
            ("train", "validation", "test"), (train_profiles, validation_profiles, test_profiles),
        )},
        "evaluation_scope": "Only explicitly judged careers in each held-out profile; labels of 2–3 count as relevant for Recall@3.",
        "metrics": evaluation,
    }
    output.mkdir(parents=True, exist_ok=False)
    artifact = output / ("model.json" if algorithm == "linear" else "model.txt")
    if algorithm == "linear":
        artifact.write_text(json.dumps({"weights": list(model.weights)}, indent=2) + "\n", encoding="utf-8")
    else:
        model.save_model(str(artifact))
    metadata = {
        **provenance, "format": model_format, "feature_names": list(FEATURE_NAMES),
        "model_sha256": sha256(artifact.read_bytes()).hexdigest(),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (output / "evaluation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="New artifact directory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--algorithm", choices=("linear", "lightgbm"), default="linear")
    args = parser.parse_args()
    try:
        report = train(args.dataset, args.catalog, args.out, args.seed, args.algorithm)
    except (OSError, ValueError, ImportError, KeyError) as error:
        parser.exit(1, f"Training failed: {error}\n")
    metrics = {key: value for key, value in report["metrics"].items() if key != "per_profile"}
    print(json.dumps({"output": str(args.out), "algorithm": report["algorithm"], "label_provenance": report["label_provenance"],
                      "splits": report["splits"], "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
