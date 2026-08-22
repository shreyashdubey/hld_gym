import asyncio
import json
import unittest

from playground import rep
from playground.grading import (
    GAP_CHAPTERS,
    build_grading_messages,
    parse_and_check,
    transcript_text,
)

TURNS = [
    {"role": "system", "content": "persona"},
    {"role": "user", "content": "we'll just shard it"},
    {"role": "assistant", "content": "What's the shard key?"},
    {"role": "user", "content": [{"type": "text", "text": "the cache goes and fetches it"}]},
]


class TestTranscriptText(unittest.TestCase):
    def test_user_turns_only_in_order(self):
        self.assertEqual(
            transcript_text(TURNS),
            "we'll just shard it\nthe cache goes and fetches it",
        )

    def test_tolerates_junk_shapes(self):
        # Turns come out of a live LLMContext; content can be a string, a
        # parts list, or absent. None of those may crash a grading pass.
        junk = [{"role": "user"}, "not a dict", {"role": "user", "content": [{"no": "text"}]}]
        self.assertEqual(transcript_text(junk), "")


class TestGradingMessages(unittest.TestCase):
    # The one place the answer key is allowed to appear: after the round.
    def test_the_grader_holds_the_answer_key(self):
        text = str(build_grading_messages(TURNS, "Components: App, Cache"))
        self.assertIn(rep.KERNEL, text)
        for label in rep.RUBRIC_LABELS:
            self.assertIn(label, text)

    def test_the_grader_sees_transcript_and_board(self):
        text = str(build_grading_messages(TURNS, "Components: App, Cache"))
        self.assertIn("we'll just shard it", text)
        self.assertIn("Components: App, Cache", text)

    def test_every_gap_area_is_offered_to_the_model(self):
        text = str(build_grading_messages(TURNS, ""))
        for key in GAP_CHAPTERS:
            self.assertIn(key, text)

    def test_the_grader_also_sees_the_interviewer_s_turns(self):
        # The probe field ("what the interviewer was pressing on") is a
        # guess unless the grader can actually see what was asked.
        text = str(build_grading_messages(TURNS, ""))
        self.assertIn("What's the shard key?", text)


class TestParseAndCheck(unittest.TestCase):
    TRANSCRIPT = "we'll just shard it\nthe cache goes and fetches it"

    def _moment(self, **over):
        m = {
            "quote": "we'll just shard it",
            "probe": "what the shard key is",
            "gap": "no shard key named",
            "gap_area": "cache_aside_vs_read_through",
        }
        m.update(over)
        return m

    def test_a_verbatim_quote_survives_with_its_chapter_resolved(self):
        got = parse_and_check('{"moments": [%s]}' % __import__("json").dumps(self._moment()), self.TRANSCRIPT)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["chapter"], GAP_CHAPTERS["cache_aside_vs_read_through"])
        self.assertNotIn("gap_area", got[0])

    def test_a_fabricated_quote_is_dropped_not_rendered(self):
        # An invented quote on a sales surface is the standing honesty rule
        # broken in the worst place: in the visitor's own mouth.
        import json
        raw = json.dumps({"moments": [self._moment(quote="I have no idea")]})
        self.assertEqual(parse_and_check(raw, self.TRANSCRIPT), [])

    def test_an_unknown_gap_area_is_dropped_the_model_does_not_mint_urls(self):
        import json
        raw = json.dumps({"moments": [self._moment(gap_area="blockchain")]})
        self.assertEqual(parse_and_check(raw, self.TRANSCRIPT), [])

    def test_at_most_three_moments(self):
        import json
        raw = json.dumps({"moments": [self._moment()] * 5})
        self.assertEqual(len(parse_and_check(raw, self.TRANSCRIPT)), 3)

    def test_zero_surviving_moments_is_a_valid_empty_map_not_a_failure(self):
        self.assertEqual(parse_and_check('{"moments": []}', self.TRANSCRIPT), [])

    def test_unparseable_json_is_none(self):
        self.assertIsNone(parse_and_check("the model rambled", self.TRANSCRIPT))

    def test_wrong_shapes_are_none_or_dropped(self):
        self.assertIsNone(parse_and_check('{"nope": 1}', self.TRANSCRIPT))
        self.assertIsNone(parse_and_check('{"moments": "x"}', self.TRANSCRIPT))
        self.assertEqual(parse_and_check('{"moments": [42, {"quote": ""}]}', self.TRANSCRIPT), [])


class TestGapChapters(unittest.TestCase):
    def test_every_chapter_link_points_into_the_free_book(self):
        for url in GAP_CHAPTERS.values():
            self.assertTrue(url.startswith("/book/#ch/"), url)


class _FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply

        class _Msg:
            content = reply

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _FakeClient:
    def __init__(self, replies):
        self.completions = _FakeCompletions(replies)

        class _Chat:
            pass

        self.chat = _Chat()
        self.chat.completions = self.completions


GOOD = json.dumps(
    {
        "moments": [
            {
                "quote": "we'll just shard it",
                "probe": "the shard key",
                "gap": "no key named",
                "gap_area": "cache_aside_vs_read_through",
            }
        ]
    }
)


class TestGrade(unittest.TestCase):
    def _grade(self, replies):
        from playground.grading import grade

        client = _FakeClient(replies)
        result = asyncio.run(
            grade(TURNS, "Components: App", model="test-model", client=client)
        )
        return result, client.completions.calls

    def test_a_good_first_reply_needs_no_retry(self):
        result, calls = self._grade([GOOD])
        self.assertEqual(len(result), 1)
        self.assertEqual(calls, 1)

    def test_unusable_output_gets_exactly_one_retry(self):
        result, calls = self._grade(["not json", GOOD])
        self.assertEqual(len(result), 1)
        self.assertEqual(calls, 2)

    def test_two_failures_is_none_never_an_exception(self):
        # A buyer must never meet a broken grader: the caller turns None into
        # the honest lost-map line, so grade() must not raise.
        result, calls = self._grade([RuntimeError("api down"), RuntimeError("api down")])
        self.assertIsNone(result)
        self.assertEqual(calls, 2)

    def test_an_empty_map_is_returned_not_retried(self):
        result, calls = self._grade([json.dumps({"moments": []})])
        self.assertEqual(result, [])
        self.assertEqual(calls, 1)

    def test_a_client_that_cannot_be_built_is_none_never_an_exception(self):
        from unittest import mock

        from playground.grading import grade

        with mock.patch("openai.AsyncOpenAI", side_effect=RuntimeError("no key")):
            result = asyncio.run(grade(TURNS, "", model="test-model"))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
