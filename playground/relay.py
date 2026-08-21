"""Sends finalized transcripts down the data channel to the browser.

Observes rather than intercepts: the frame keeps flowing, because Playground
needs the same transcription to reach the context aggregator behind this.
"""

from pipecat.frames.frames import Frame, OutputTransportMessageUrgentFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class TranscriptRelay(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # Interim frames rewrite themselves as the model changes its mind;
        # appending them to a textarea makes the answer stutter.
        if isinstance(frame, TranscriptionFrame) and frame.finalized and frame.text.strip():
            await self.push_frame(
                OutputTransportMessageUrgentFrame(
                    message={"type": "transcript", "text": frame.text}
                )
            )

        await self.push_frame(frame, direction)
