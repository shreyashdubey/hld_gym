import unittest

from pipecat.frames.frames import InterimTranscriptionFrame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection

from playground.relay import TranscriptRelay


class Captured:
    """Stands in for the rest of the pipeline. Records what got pushed."""

    def __init__(self):
        self.frames = []


def run(frame):
    """Drive one frame through a relay and return what it pushed downstream."""
    import asyncio

    relay = TranscriptRelay()
    got = Captured()

    async def fake_push(f, direction=FrameDirection.DOWNSTREAM):
        got.frames.append(f)

    relay.push_frame = fake_push
    asyncio.run(relay.process_frame(frame, FrameDirection.DOWNSTREAM))
    return got.frames


class TestTranscriptRelay(unittest.TestCase):
    def test_finalized_transcription_becomes_a_client_message(self):
        out = run(
            TranscriptionFrame(
                text="the app checks the cache first",
                user_id="u",
                timestamp="t",
                finalized=True,
            )
        )
        messages = [f.message for f in out if hasattr(f, "message")]
        self.assertIn(
            {"type": "transcript", "text": "the app checks the cache first"}, messages
        )

    def test_interim_transcription_is_not_sent(self):
        """Interim text rewrites itself as the model changes its mind. Appending
        it to a textarea would make the answer stutter."""
        out = run(InterimTranscriptionFrame(text="the app che", user_id="u", timestamp="t"))
        messages = [f.message for f in out if hasattr(f, "message")]
        self.assertEqual(messages, [])

    def test_non_finalized_transcription_frame_is_not_sent(self):
        """TranscriptionFrame(finalized=False) -- not InterimTranscriptionFrame --
        is the actual shape a non-finalized transcription takes. It is inert
        today because SegmentedSTTService force-sets finalized=True on
        everything it emits, but the guard must still hold on its own: it stops
        being inert the moment the STT service is swapped for a streaming one."""
        out = run(
            TranscriptionFrame(text="the app che", user_id="u", timestamp="t", finalized=False)
        )
        messages = [f.message for f in out if hasattr(f, "message")]
        self.assertEqual(messages, [])

    def test_the_original_frame_still_flows_downstream(self):
        """The relay observes; it must not swallow. Playground needs the same
        frame to reach the context aggregator."""
        frame = TranscriptionFrame(text="hello", user_id="u", timestamp="t", finalized=True)
        out = run(frame)
        self.assertIn(frame, out)

    def test_unrelated_frames_pass_through_untouched(self):
        frame = TextFrame(text="not a transcript")
        out = run(frame)
        self.assertEqual(out, [frame])


if __name__ == "__main__":
    unittest.main()
