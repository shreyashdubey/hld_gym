"""Both pipelines. Dictation is the Playground pipeline with the LLM and TTS
stages removed, which is the reason they share a service."""

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from playground.config import VoiceConfig
from playground.relay import TranscriptRelay


def _vad(config: VoiceConfig, stop_secs: float) -> VADProcessor:
    """In pipecat 1.7 the VAD is a pipeline processor, not a transport field."""
    return VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(
                confidence=config.confidence,
                start_secs=config.start_secs,
                stop_secs=stop_secs,
                min_volume=config.min_volume,
            )
        )
    )


def build_dictation_worker(
    connection: SmallWebRTCConnection, config: VoiceConfig
) -> PipelineWorker:
    """mic -> VAD -> STT -> data channel. No LLM, no TTS, nothing talks back."""
    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=False),
    )
    stt = OpenAISTTService(settings=OpenAISTTService.Settings(model="gpt-4o-transcribe"))
    pipeline = Pipeline(
        [
            transport.input(),
            _vad(config, config.dictation_stop_secs),
            stt,
            TranscriptRelay(),
            transport.output(),
        ]
    )
    return PipelineWorker(pipeline, params=PipelineParams(enable_metrics=True))
