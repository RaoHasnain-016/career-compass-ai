"""Pure unit tests for recommendation scoring and the admin role guard.

Run from backend with: python -m unittest discover -s tests -v
These tests use simple in-memory objects only; no database, Firebase, or
external provider is contacted.
"""

from types import SimpleNamespace
import unittest

from fastapi import HTTPException

from app.routes.admin_routes import require_admin
from app.services.recommendation_service import (
    calculate_academic_score,
    calculate_percentage_match,
    generate_recommendation_analysis,
)


class RecommendationScoringTests(unittest.TestCase):
    def profile(self, **overrides):
        data = {
            "academic_level": "Intermediate",
            "marks_cgpa": 80,
            "interests": [" Technology ", "Design"],
            "skills": ["Python", "Communication"],
            "favorite_subjects": ["Mathematics"],
            "study_preference": "online practical",
            "country": "Pakistan",
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    def career(self, **overrides):
        data = {
            "title": "Software Engineer",
            "field": "Technology",
            "minimum_marks": 70,
            "related_interests": ["technology", "science"],
            "required_skills": ["python", "SQL"],
            "required_subjects": ["mathematics", "physics"],
            "required_education": "Intermediate",
            "difficulty_level": "moderate",
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    def test_weighted_score_normalizes_case_and_whitespace(self):
        analysis = generate_recommendation_analysis(self.profile(), self.career())

        # 20 academic + 12.5 interests + 12.5 skills + 10 subjects + 10 preference.
        self.assertEqual(analysis["score"], 65.0)
        self.assertEqual(analysis["confidence_level"], "Strong Match")
        self.assertEqual(analysis["eligibility_status"], "eligible")
        self.assertEqual(analysis["matched_interests"], ["technology"])
        self.assertEqual(analysis["missing_skills"], ["sql"])

    def test_foundation_stage_caps_academic_component(self):
        score, status = calculate_academic_score(
            self.profile(academic_level="Matric", marks_cgpa=90), self.career()
        )

        self.assertEqual(score, 9.0)
        self.assertEqual(status, "foundation_stage")

    def test_diploma_stage_is_not_immediately_eligible_for_bachelor_only_path(self):
        score, status = calculate_academic_score(
            self.profile(academic_level="Diploma / DAE", marks_cgpa=80),
            self.career(required_education="Bachelor degree"),
        )

        self.assertEqual(score, 8.0)
        self.assertEqual(status, "foundation_stage")

    def test_empty_career_requirements_do_not_create_a_match(self):
        percentage, matched, missing = calculate_percentage_match(["Python"], [])

        self.assertEqual(percentage, 0)
        self.assertEqual(matched, [])
        self.assertEqual(missing, [])

    def test_gpa_is_normalized_before_academic_eligibility(self):
        profile = self.profile(
            marks_cgpa=3.5,
            study_preference="online practical | Academic scale: GPA out of 4",
        )
        score, status = calculate_academic_score(profile, self.career(minimum_marks=80))

        self.assertEqual(score, 20)
        self.assertEqual(status, "eligible")

    def test_equivalent_subject_and_skill_terms_match_by_concept(self):
        skill_ratio, matched_skills, missing_skills = calculate_percentage_match(
            ["Python"], ["Programming", "Database"]
        )
        subject_ratio, matched_subjects, missing_subjects = calculate_percentage_match(
            ["Arts & Design"], ["Arts"]
        )

        self.assertEqual(skill_ratio, 0.5)
        self.assertEqual(matched_skills, ["programming"])
        self.assertEqual(missing_skills, ["database"])
        self.assertEqual(subject_ratio, 1)
        self.assertEqual(matched_subjects, ["arts"])
        self.assertEqual(missing_subjects, [])


class AdminAuthorizationTests(unittest.TestCase):
    def test_admin_role_is_accepted_case_insensitively(self):
        self.assertIsNone(require_admin(SimpleNamespace(role="ADMIN")))

    def test_student_role_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            require_admin(SimpleNamespace(role="student"))

        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(error.exception.detail, "Admin access required.")


if __name__ == "__main__":
    unittest.main()
