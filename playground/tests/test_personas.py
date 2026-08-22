import pathlib
import re
import unittest

from playground import rep
from playground.config import VoiceConfig
from playground.personas import COACH_PROMPT, DIAGNOSTIC_PROMPT, INTERVIEWER_PROMPT
from playground.session import Session

REP_TS = pathlib.Path(__file__).resolve().parents[2] / "sell" / "lib" / "rep.ts"


class TestPersonas(unittest.TestCase):
    def test_the_interviewer_does_not_hold_the_answers(self):
        """A model holding the answers leaks them the moment a candidate sounds
        stuck, and then the round graded nothing."""
        prompt = INTERVIEWER_PROMPT
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertNotIn(label, prompt)

    def test_the_coach_does_hold_the_answers(self):
        prompt = COACH_PROMPT
        for probe in rep.PROBES:
            self.assertIn(probe["a"], prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertIn(label, prompt)

    def test_the_interviewer_still_knows_the_question(self):
        self.assertIn(rep.REP_TITLE, INTERVIEWER_PROMPT)

    def test_the_two_prompts_are_not_the_same_text(self):
        self.assertNotEqual(INTERVIEWER_PROMPT, COACH_PROMPT)


class TestNoDriftFromTheFrontend(unittest.TestCase):
    """Python cannot import sell/lib/rep.ts, so the rubric exists twice. This is
    the guard that stops the two copies quietly disagreeing."""

    def test_rep_title_matches_rep_ts(self):
        """REP_TITLE is what the interviewer prompt interpolates
        (test_the_interviewer_still_knows_the_question above uses the
        Python copy alone) -- it drifted out of this guard's reach when the
        rubric/probe checks were added, the same class of gap as either of
        those would leave if it went unchecked."""
        source = REP_TS.read_text()
        match = re.search(r'export const REP_TITLE = "([^"]+)"', source)
        self.assertIsNotNone(match, "REP_TITLE not found in rep.ts")
        self.assertEqual(match.group(1), rep.REP_TITLE)

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


class TestDiagnosticPrompt(unittest.TestCase):
    def test_the_diagnostic_interviewer_is_starved_of_the_answer_key(self):
        # Same invariant as the sprint interviewer: a model holding the
        # answers leaks them the moment a candidate sounds stuck, and then
        # the round graded nothing.
        prompt = DIAGNOSTIC_PROMPT
        self.assertNotIn(rep.KERNEL, prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertNotIn(label, prompt)
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], prompt)

    def test_it_still_names_the_rep_and_end_round(self):
        prompt = DIAGNOSTIC_PROMPT
        self.assertIn(rep.REP_TITLE, prompt)
        self.assertIn("end_round", prompt)

    def test_a_diagnostic_session_uses_the_diagnostic_prompt(self):
        s = Session(VoiceConfig(), kind="diagnostic")
        self.assertIn(DIAGNOSTIC_PROMPT, s.system_messages()[0]["content"])


if __name__ == "__main__":
    unittest.main()
