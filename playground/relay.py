"""Sends finalized transcripts down the data channel to the browser.

Observes rather than intercepts: the frame keeps flowing, because Playground
needs the same transcription to reach the context aggregator behind this.
"""

from pipecat.frames.frames import Frame, OutputTransportMessageUrgentFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

RTVI_LABEL = "rtvi-ai"


def server_message(data: dict) -> dict:
    """Wrap an app payload in the envelope pipecat's own RTVIProcessor uses
    for server-to-client messages (see ``ServerMessage`` in
    ``pipecat/processors/frameworks/rtvi/models.py``: ``label="rtvi-ai"``,
    ``type="server-message"``). ``@pipecat-ai/small-webrtc-transport`` only
    bubbles an inbound data-channel message up to ``onServerMessage`` when
    ``messageObj.label === "rtvi-ai"`` -- an unlabelled message, like a bare
    ``{"type": "transcript", ...}``, is parsed off the wire and then silently
    dropped, never reaching the app's ``onMessage`` callback. The client then
    hands the callback just ``data`` back (client-js:
    ``onServerMessage?.(ev.data)``), so callers here keep writing the same
    flat ``{"type": ..., ...}`` payloads as ``data``."""
    return {"label": RTVI_LABEL, "type": "server-message", "data": data}


class TranscriptRelay(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # Interim frames rewrite themselves as the model changes its mind;
        # appending them to a textarea makes the answer stutter.
        if isinstance(frame, TranscriptionFrame) and frame.finalized and frame.text.strip():
            await self.push_frame(
                OutputTransportMessageUrgentFrame(
                    message=server_message({"type": "transcript", "text": frame.text})
                )
            )

        await self.push_frame(frame, direction)
