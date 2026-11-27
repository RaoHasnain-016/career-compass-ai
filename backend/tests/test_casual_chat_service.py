from unittest import TestCase

from app.services.casual_chat_service import answer_casual_chat


class CasualChatTests(TestCase):
    def test_greetings_support_case_punctuation_and_salutation_spellings(self):
        self.assertTrue(answer_casual_chat("  HI!! 👋  ").startswith("Hi!"))
        for message in ("AOA", "A.O.A!", "Assalam-o-alaikum", "AOA, kya haal hai?"):
            with self.subTest(message=message):
                self.assertTrue(answer_casual_chat(message).startswith("Wa alaikum assalam!"))
        self.assertTrue(answer_casual_chat("السَّلَامُ عَلَيْكُمْ!").startswith("وعلیکم السلام!"))

    def test_short_courtesies_use_the_students_language(self):
        self.assertEqual(answer_casual_chat("Thank you!"), "You’re welcome!")
        self.assertIn("مدد", answer_casual_chat("آپ کیسے ہیں؟"))
        self.assertIn("madad", answer_casual_chat("Kya haal hai?"))
        self.assertIn("کیریئر کمپاس", answer_casual_chat("آپ کون ہیں؟"))
        self.assertIn("Allah hafiz", answer_casual_chat("Allah Hafiz!"))

    def test_substantive_questions_and_followups_are_left_to_normal_routing(self):
        for question in (
            "Hi, which software career fits me?",
            "AOA kya admissions khule hain?",
            "السلام علیکم، آخری تاریخ کیا ہے؟",
            "Thanks, please compare these careers.",
            "Can you help me calculate 20% of 80?",
            "Hello! Is it safe to accept this job?",
            "Yes",
            "",
        ):
            with self.subTest(question=question):
                self.assertIsNone(answer_casual_chat(question))
