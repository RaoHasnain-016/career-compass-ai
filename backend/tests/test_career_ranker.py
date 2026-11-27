"""Offline ranker policy and training-data checks without a database."""

from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app.services import career_ranker
from ml.train_career_ranker import (
    DEFAULT_CATALOG, DEFAULT_DATASET, _profile_metrics, load_catalog,
    load_judgments, split_by_group,
)


class FileDatasetTests(unittest.TestCase):
    def test_catalog_and_explicit_labels_make_disjoint_profile_splits(self):
        catalog = load_catalog(DEFAULT_CATALOG)
        profiles, provenance = load_judgments(DEFAULT_DATASET, catalog)
        self.assertGreaterEqual(len(profiles), 36)
        self.assertEqual(provenance["label_provenance"], "synthetic_authored")
        self.assertTrue(any(candidate.relevance == 0 for profile in profiles for candidate in profile.candidates))

        train, validation, test = split_by_group(profiles, 42)
        split_ids = [{profile.group_id for profile in part} for part in (train, validation, test)]
        self.assertTrue(all(split_ids))
        self.assertEqual(len(set.union(*split_ids)), sum(map(len, split_ids)))
        self.assertEqual(sum(map(len, (train, validation, test))), len(profiles))

    def test_ranking_metrics_distinguish_relevance_and_order(self):
        self.assertEqual(_profile_metrics([3, 2, 0, 0]), {"ndcg_at_3": 1.0, "recall_at_3": 1.0})
        self.assertLess(_profile_metrics([2, 3, 0, 0])["ndcg_at_3"], 1)
        self.assertEqual(_profile_metrics([3, 0, 0, 2])["recall_at_3"], 0.5)


class LocalRankerTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(DEFAULT_CATALOG)
        self.profile = SimpleNamespace(
            academic_level="Diploma / DAE", country="Pakistan", marks_cgpa=3.6,
            study_preference="Practical | Academic scale: GPA out of 4",
            interests=["Technology"], skills=["Networking"], favorite_subjects=["Computer Science"],
        )
        self.rows = [
            SimpleNamespace(career=self.catalog["Software Engineer"], match_score=70.5, eligibility_status="foundation_stage"),
            SimpleNamespace(career=self.catalog["IT Support Technician"], match_score=55, eligibility_status="eligible"),
        ]

    def test_shared_features_normalize_gpa_and_separate_eligibility(self):
        features = career_ranker.career_rank_features(self.profile, self.rows[0].career)
        self.assertEqual(len(features), len(career_ranker.FEATURE_NAMES))
        self.assertEqual(features[career_ranker.FEATURE_NAMES.index("grade_normalized")], 0.9)
        self.assertEqual(features[career_ranker.FEATURE_NAMES.index("foundation_path")], 1)

    def test_off_by_default_avoids_any_load(self):
        with patch.dict(os.environ, {"CAREER_RANKER_DIR": ""}), patch.object(career_ranker, "_load_ranker") as load:
            self.assertEqual(career_ranker.rank_recommendations(self.profile, self.rows), (self.rows, "rules"))
        load.assert_not_called()

    def test_eligibility_guard_preserves_score_evidence(self):
        fake_ranker = Mock()
        fake_ranker.predict.return_value = [8.0, 0.1]
        with patch.dict(os.environ, {"CAREER_RANKER_DIR": "pilot-model"}), patch.object(career_ranker, "_load_ranker", return_value=fake_ranker):
            ordered, source = career_ranker.rank_recommendations(self.profile, self.rows)
        self.assertEqual(source, "trained")
        self.assertEqual(ordered, list(reversed(self.rows)))
        self.assertEqual([item.match_score for item in self.rows], [70.5, 55])
        self.assertEqual(self.rows[0].eligibility_status, "foundation_stage")

    def test_incompatible_metadata_does_not_load_model(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "model.txt").write_text("invalid text", encoding="utf-8")
            (path / "metadata.json").write_text('{"format":"incompatible"}', encoding="utf-8")
            with patch.dict(os.environ, {"CAREER_RANKER_DIR": temp}), self.assertLogs(career_ranker.logger, "WARNING"):
                self.assertEqual(career_ranker.rank_recommendations(self.profile, self.rows), (self.rows, "rules"))

    def test_invalid_model_output_preserves_rule_order(self):
        fake_ranker = Mock()
        fake_ranker.predict.return_value = [float("nan"), 0]
        with (patch.dict(os.environ, {"CAREER_RANKER_DIR": "pilot-model"}),
              patch.object(career_ranker, "_load_ranker", return_value=fake_ranker),
              self.assertLogs(career_ranker.logger, "WARNING")):
            self.assertEqual(career_ranker.rank_recommendations(self.profile, self.rows), (self.rows, "rules"))

    def test_portable_weights_load_without_lightgbm(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            weights = [1.0] * len(career_ranker.FEATURE_NAMES)
            artifact = json.dumps({"weights": weights}).encode("utf-8")
            (path / "model.json").write_bytes(artifact)
            (path / "metadata.json").write_text(json.dumps({
                "format": career_ranker.LINEAR_MODEL_FORMAT,
                "feature_names": list(career_ranker.FEATURE_NAMES),
                "model_sha256": sha256(artifact).hexdigest(),
            }), encoding="utf-8")
            loaded = career_ranker._load_ranker(path)
            self.assertEqual(loaded.predict([[2.0] * len(weights)]), [2.0 * len(weights)])
