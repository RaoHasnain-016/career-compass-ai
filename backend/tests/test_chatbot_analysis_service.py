import json
import unittest

from app.services.chatbot_analysis_service import answer_profile_analysis


class ProfileAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.data_analyst = {
            "title": "Data Analyst", "match_score": 86.5, "matched_skills": ["Excel"],
            "matched_subjects": ["Statistics"], "missing_skills": ["SQL", "Data Cleaning"],
            "eligibility_status": "near_eligible",
        }
        self.web_developer = {
            "title": "Web Developer", "match_score": 74, "matched_skills": ["HTML"],
            "missing_skills": ["CSS"], "eligibility_status": "foundation_stage",
        }
        self.data = {
            "profile": {"academic_level": "Intermediate", "skills": ["Excel", "HTML"], "class_degree": "ICS"},
            "selected_career": {"title": "Data Analyst", "required_skills": ["Excel", "SQL", "Data Cleaning"]},
            "recommendations": [self.data_analyst, self.web_developer],
            "roadmap": [{"title": "Clean a dataset", "stage_order": 1, "required_skills": ["Data Cleaning"]}],
            "learning_resources": [{"title": "Study SQL", "skill": "SQL"}],
        }

    def ask(self, message):
        return answer_profile_analysis(message, json.dumps(self.data))

    def test_why_explains_selected_match_and_academic_stage(self):
        reply = self.ask("Why was this career recommended?")
        self.assertIn("Data Analyst has a profile match of 86.5%", reply)
        self.assertIn("Excel", reply)
        self.assertIn("Statistics", reply)
        self.assertIn("academic requirements", reply)
        self.assertNotIn("Web Developer", reply)

    def test_compare_uses_saved_rank_and_honors_named_order(self):
        ranked = self.ask("Compare my top two careers.")
        self.assertLess(ranked.index("Data Analyst"), ranked.index("Web Developer"))
        self.assertIn("86.5%", ranked)
        self.assertIn("74%", ranked)
        named = self.ask("Compare Web Developer and Data Analyst.")
        self.assertLess(named.index("Web Developer"), named.index("Data Analyst"))

    def test_skill_priority_uses_next_step_before_available_resource(self):
        reply = self.ask("Which skill gap matters most?")
        self.assertIn("Data Cleaning", reply)
        self.assertIn("roadmap", reply)
        self.assertNotIn("SQL", reply)
        self.data["roadmap"] = []
        reply = self.ask("Which skill gap matters most?")
        self.assertIn("SQL", reply)
        self.assertIn("resource", reply)

    def test_missing_or_unrelated_comparison_asks_for_evidence(self):
        self.data["recommendations"] = [self.data_analyst]
        reply = self.ask("Compare my top two careers.")
        self.assertIn("Which two", reply)
        self.assertNotIn("Web Developer", reply)
        self.assertIn("Which two", self.ask("Compare nursing and architecture careers."))
        self.assertIsNone(self.ask("Compare two phones."))
        self.assertIn("What are you studying", answer_profile_analysis("Why was this career recommended?", "{}"))
        self.assertIn("What are you studying", answer_profile_analysis("Why was this career recommended?", "not json"))

    def test_ordinal_follow_up_uses_displayed_order_and_requires_context(self):
        self.assertIsNone(self.ask("Why the first one?"))
        self.data["recent_chat"] = [{
            "question": "Compare Web Developer and Data Analyst.",
            "response": "Here's the comparison. Web Developer has a 74% match. Data Analyst has a 86.5% match.",
        }]
        self.assertIn("Web Developer", self.ask("Why the first one?"))
        self.assertNotIn("Data Analyst", self.ask("Why the first one?"))
        self.assertIn("Data Analyst", self.ask("Why the second one?"))

    def test_program_options_and_localized_match_avoid_admission_claims(self):
        self.assertIn("top matches", self.ask("What career options are there for my degree?"))
        self.assertIn("ICS", self.ask("What career options are there for my degree?"))
        self.assertIn("Data Analyst", self.ask("Career options for my degree."))
        self.assertIn("profile se", self.ask("Yeh career kyun recommend hua?"))
        self.assertIn("فیصد", self.ask("اس کیریئر کی سفارش کیوں ہوئی؟"))
        for message in ("Compare degree admission deadlines.", "Will I get a scholarship if I choose this career?"):
            self.assertIsNone(self.ask(message))

    def test_school_comparison_points_to_subjects_and_avoids_invented_scores(self):
        self.data["profile"]["academic_level"] = "Matric"
        self.data_analyst["match_score"] = float("nan")
        reply = self.ask("Compare my top two careers.")
        self.assertEqual(reply.count("At your school stage"), 1)
        self.assertIn("subject groups", reply)
        self.assertNotIn("nan%", reply)


if __name__ == "__main__":
    unittest.main()
