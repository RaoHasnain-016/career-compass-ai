"""Optional server-side ranking from a trusted local LightGBM artifact."""

from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
import json
import logging
from math import isfinite
import os
from pathlib import Path
from threading import Lock

from app.services.recommendation_service import (
    calculate_academic_score,
    calculate_percentage_match,
    calculate_preference_score,
    normalize_academic_score,
    normalize_list,
)


logger = logging.getLogger(__name__)
MODEL_FORMAT = "career-compass-lightgbm-v1"
LINEAR_MODEL_FORMAT = "career-compass-linear-v1"
ACTIONABLE_ELIGIBILITY = {"eligible", "near_eligible"}
PREFERENCE_BOOSTS = {"saved_career": 8, "saved_field": 4}
FEEDBACK_SIGNALS = {"helpful": 1, "less_relevant": -1}
_load_lock = Lock()
FEATURE_NAMES = (
    "interest_overlap", "skill_overlap", "subject_overlap",
    "exact_interest_overlap", "exact_skill_overlap", "exact_subject_overlap",
    "grade_normalized", "grade_missing", "academic_readiness",
    "foundation_path", "near_eligible", "below_requirement", "study_preference_fit",
)


def _overlaps(student_values, career_values):
    semantic_ratio, _, _ = calculate_percentage_match(student_values, career_values)
    career_values = normalize_list(career_values)
    exact_ratio = len(normalize_list(student_values) & career_values) / len(career_values) if career_values else 0
    return semantic_ratio, exact_ratio


def career_rank_features(profile, career):
    """Same feature values and order for training and local inference."""
    interest, exact_interest = _overlaps(profile.interests, career.related_interests)
    skill, exact_skill = _overlaps(profile.skills, career.required_skills)
    subject, exact_subject = _overlaps(profile.favorite_subjects, career.required_subjects)
    academic, eligibility = calculate_academic_score(profile, career)
    return [
        interest, skill, subject, exact_interest, exact_skill, exact_subject,
        normalize_academic_score(profile) / 100,
        float(profile.marks_cgpa is None),
        academic / 20,
        float(eligibility == "foundation_stage"),
        float(eligibility == "near_eligible"),
        float(eligibility == "below_requirement"),
        calculate_preference_score(profile, career) / 10,
    ]


def ranking_policy_key(eligibility, learned_score, baseline_score, title):
    """Rank actionable candidates before aspirational or unqualified ones."""
    later_path = eligibility not in ACTIONABLE_ELIGIBILITY
    return later_path, -learned_score, -baseline_score, title.casefold()


def personalize_recommendations(recommendations, saved_careers, feedback=None):
    """Adapt one student's order from their current ratings and bookmarks."""
    feedback = feedback or {}
    saved_ids = {career_id for career_id, _ in saved_careers}
    saved_fields = {field.strip().casefold() for _, field in saved_careers if field and field.strip()}
    field_signals = defaultdict(list)
    for item in recommendations:
        field = (item.career.field or "").strip().casefold()
        signal = FEEDBACK_SIGNALS.get(feedback.get(item.career_id))
        if field and signal and item.career.status:
            field_signals[field].append(signal)
    # Give related careers a small adjustment, with two neutral observations
    # so a single rating does not outweigh a direct career preference.
    field_weights = {field: 6 * sum(signals) / (len(signals) + 2) for field, signals in field_signals.items()}

    reasons = {}
    adjustments = {}
    for item in recommendations:
        if item.eligibility_status not in ACTIONABLE_ELIGIBILITY or not item.career.status:
            continue
        value = feedback.get(item.career_id)
        field = (item.career.field or "").strip().casefold()
        related_weight = field_weights.get(field, 0)
        if value in FEEDBACK_SIGNALS:
            reason, adjustment = f"feedback_{value}", 12 * FEEDBACK_SIGNALS[value]
        elif item.career_id in saved_ids:
            reason, adjustment = "saved_career", PREFERENCE_BOOSTS["saved_career"]
        elif related_weight:
            reason = "feedback_field_helpful" if related_weight > 0 else "feedback_field_less_relevant"
            adjustment = related_weight
        elif field in saved_fields:
            reason, adjustment = "saved_field", PREFERENCE_BOOSTS["saved_field"]
        else:
            continue
        reasons[item.career_id] = reason
        adjustments[item.career_id] = adjustment

    if not reasons:
        return recommendations, reasons

    ordered = sorted(recommendations, key=lambda item: (
        item.eligibility_status not in ACTIONABLE_ELIGIBILITY,
        -float(item.match_score) - adjustments.get(item.career_id, 0),
    ))
    return ordered, reasons


def ranker_configured():
    return bool(os.getenv("CAREER_RANKER_DIR", "").strip())


class _LoadedRanker:
    def __init__(self, booster):
        self.booster = booster
        self.lock = Lock()

    def predict(self, features):
        from numpy import asarray

        with self.lock:
            return self.booster.predict(asarray(features, dtype="float64"), num_threads=1)


class _LinearRanker:
    def __init__(self, weights):
        self.weights = tuple(weights)

    def predict(self, features):
        return [sum(weight * value for weight, value in zip(self.weights, row)) for row in features]


@lru_cache(maxsize=4)
def _load_ranker(directory):
    try:
        metadata_path = directory / "metadata.json"
        if metadata_path.stat().st_size > 64_000:
            raise ValueError("Metadata exceeds expected size")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_format = metadata["format"]
        if model_format not in {MODEL_FORMAT, LINEAR_MODEL_FORMAT}:
            raise ValueError("Unknown artifact format")
        model_path = directory / ("model.json" if model_format == LINEAR_MODEL_FORMAT else "model.txt")
        if model_path.stat().st_size > 20_000_000:
            raise ValueError("Model exceeds expected size")
        if (
            metadata["feature_names"] != list(FEATURE_NAMES)
            or sha256(model_path.read_bytes()).hexdigest() != metadata["model_sha256"]
        ):
            raise ValueError("Artifact metadata mismatch")

        if model_format == LINEAR_MODEL_FORMAT:
            weights = json.loads(model_path.read_text(encoding="utf-8"))["weights"]
            if len(weights) != len(FEATURE_NAMES) or not all(
                type(weight) in (int, float) and isfinite(weight) and abs(weight) <= 100 for weight in weights
            ):
                raise ValueError("Invalid linear model weights")
            return _LinearRanker(weights)

        from lightgbm import Booster

        booster = Booster(model_file=str(model_path))
        if booster.feature_name() != list(FEATURE_NAMES) or booster.num_trees() == 0:
            raise ValueError("Model feature or tree mismatch")
        return _LoadedRanker(booster)
    except Exception as exc:
        logger.warning("Local career ranker unavailable (%s); using rule order", type(exc).__name__)
        return None


def rank_recommendations(profile, recommendations):
    """Reorder pre-scored rows by local model, preserving their rule evidence."""
    directory = os.getenv("CAREER_RANKER_DIR", "").strip()
    if not directory or profile is None or len(recommendations) < 2:
        return recommendations, "rules"
    try:
        with _load_lock:
            ranker = _load_ranker(Path(directory).expanduser().resolve())
        if ranker is None:
            return recommendations, "rules"
        features = [career_rank_features(profile, item.career) for item in recommendations]
        scores = [float(score) for score in ranker.predict(features)]
        if len(scores) != len(recommendations) or not all(isfinite(score) for score in scores):
            raise ValueError("Model returned invalid scores")
        if len(set(scores)) == 1:
            return recommendations, "rules"
        ranked = sorted(zip(recommendations, scores), key=lambda pair: ranking_policy_key(
            pair[0].eligibility_status,
            pair[1], float(pair[0].match_score), pair[0].career.title,
        ))
        return [item for item, _ in ranked], "trained"
    except Exception as exc:
        logger.warning("Local career prediction failed (%s); using rule order", type(exc).__name__)
        return recommendations, "rules"
