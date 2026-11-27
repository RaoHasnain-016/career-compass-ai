from unittest import TestCase

from app.services.general_chat_service import answer_general_question


class GeneralChatTests(TestCase):
    def test_grade_and_discount_calculations_show_steps(self):
        self.assertIn("**80%**", answer_general_question("I got 72 out of 90, what is my percentage?"))
        self.assertIn("**36**", answer_general_question("What is 15% of 240?"))
        self.assertIn("total cannot be zero", answer_general_question("8 out of 0"))

    def test_explanations_preserve_question_language(self):
        self.assertIn("programming language", answer_general_question("What is Python?"))
        self.assertIn("ek programming language", answer_general_question("Python kya hai?"))
        self.assertIn("پروگرامنگ زبان", answer_general_question("پائتھن کیا ہے؟"))

    def test_general_question_matching_leaves_personal_questions_alone(self):
        self.assertIsNone(answer_general_question("What is my Python skill gap?"))
        self.assertIsNone(answer_general_question("Explain my diploma admission requirements"))
        self.assertIsNone(answer_general_question("2 + 2 and what career should I choose?"))
