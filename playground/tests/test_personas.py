import pathlib
import re
import unittest

from playground import rep
from playground.personas import coach_prompt, interviewer_prompt

REP_TS = pathlib.Path(__file__).resolve().parents[2] / "sell" / "lib" / "rep.ts"


class TestPersonas(unittest.TestCase):
    def test_the_interviewer_does_not_hold_the_answers(self):
        """A model holding the answers leaks them the moment a candidate sounds
        stuck, and then the round graded nothing."""
        prompt = interviewer_prompt()
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertNotIn(label, prompt)

    def test_the_coach_does_hold_the_answers(self):
        prompt = coach_prompt()
        for probe in rep.PROBES:
            self.assertIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertIn(label, prompt)

    def test_the_interviewer_still_knows_the_question(self):
        self.assertIn(rep.REP_TITLE, interviewer_prompt())

    def test_the_two_prompts_are_not_the_same_text(self):
        self.assertNotEqual(interviewer_prompt(), coach_prompt())


class TestNoDriftFromTheFrontend(unittest.TestCase):
    """Python cannot import sell/lib/rep.ts, so the rubric exists twice. This is
    the guard that stops the two copies quietly disagreeing."""

    def test_rubric_labels_match_rep_ts(self):
        source = REP_TS.read_text()
        block = source.split("export const RUBRIC")[1].split("];")[0]
        labels = re.findall(r'label:\s*"([^"]+)"', block)
        self.assertEqual(labels, rep.RUBRIC_LABELS)

    def test_probe_questions_match_rep_ts(self):
        source = REP_TS.read_text()
        block = source.split("export const PROBES")[1].split("];")[0]
        questions = re.findall(r'q:\s*"((?:[^"\\]|\\.)*)"', block)
        answers = re.findall(r'a:\s*"((?:[^"\\]|\\.)*)"', block)
        # A bare length check would pass even if a question or answer had
        # drifted in content, not just count. Compare the text too.
        self.assertEqual(questions, [p["q"] for p in rep.PROBES])
        self.assertEqual(answers, [p["a"] for p in rep.PROBES])


if __name__ == "__main__":
    unittest.main()
