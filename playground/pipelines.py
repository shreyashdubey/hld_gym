"""Both pipelines. Dictation is the Playground pipeline with the LLM and TTS
stages removed, which is the reason they share a service."""

import asyncio
from functools import partial

from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.turns.user_stop import TurnAnalyzerUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from playground.config import VoiceConfig
from playground.relay import TranscriptRelay, server_message
from playground.session import Session


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
    stt = OpenAISTTService(settings=OpenAISTTService.Settings(model=config.stt_model))
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


async def _end_round(session: Session, tts: OpenAITTSService, params) -> None:
    """Handler for the end_round tool call: the interviewer becomes the coach,
    the context is refreshed to admit the answer key, and the handoff is made
    audible. Module-level (bound to its session/tts via functools.partial in
    build_playground_worker) so test_pipelines.py can call it directly against
    a stub tts and a bound fake context -- a dropped switch_to_coach(), a
    dropped push_context(), or a dropped set_voice() must fail a test, not
    just look right in a diff."""
    session.switch_to_coach()
    session.push_context()
    # set_voice is deprecated (removed in 2.0.0, TTSUpdateSettingsFrame is
    # the replacement) but still functional in 1.7.0, and this is the only
    # place a voice change is needed -- the audible half of the handoff.
    await tts.set_voice(session.tts_voice())
    await params.result_callback({"ok": True})


async def _end_diagnostic_round(session: Session, on_round_end, params) -> None:
    """Handler for end_round in a diagnostic session: no coach, no voice
    switch -- the round ends in a written failure map instead. Ack first so
    the pipeline is never left waiting on a tool result, then hand off to
    the server's end path (grading, delivery, teardown) as its own task:
    grading is a full LLM call and this callback runs inside the pipeline's
    own processing."""
    await params.result_callback({"ok": True})
    if on_round_end is not None:
        asyncio.create_task(on_round_end(session))


async def _draw_diagram(connection: SmallWebRTCConnection, params) -> None:
    """Handler for the draw_diagram tool call.

    connection.send_app_message, not transport.output().push_frame:
    push_frame is meant to be called from inside a FrameProcessor's own
    process_frame(), not from an arbitrary function-call callback: it gates
    on the processor already having seen a StartFrame (_check_started) and
    there's no guarantee of that here. The connection is already in scope and
    already queues if the data channel isn't open yet.

    server_message() wraps this in the rtvi-ai envelope the client's
    transport requires to bubble a message up to onServerMessage at all --
    see playground/relay.py."""
    connection.send_app_message(server_message({"type": "draw", "topology": params.arguments}))
    await params.result_callback({"drawn": True})


def build_playground_worker(
    connection: SmallWebRTCConnection,
    config: VoiceConfig,
    kind: str = "sprint",
    on_round_end=None,
) -> tuple[PipelineWorker, Session]:
    """mic -> VAD -> STT -> context -> LLM -> TTS -> speaker.

    The interviewer never sees the answer key (playground.personas); the key
    enters the session only when end_round calls session.switch_to_coach().
    """
    session = Session(config, kind=kind)

    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    )
    stt = OpenAISTTService(settings=OpenAISTTService.Settings(model=config.stt_model))
    llm = OpenAILLMService(settings=OpenAILLMService.Settings(model=config.llm_model))
    tts = OpenAITTSService(
        settings=OpenAITTSService.Settings(model=config.tts_model, voice=session.tts_voice())
    )

    context = LLMContext(messages=session.system_messages())
    # session.tools() is END_ROUND-only in interview mode (the session's
    # starting mode) -- the interviewer never gets draw_diagram. See
    # playground/session.py: push_context() re-sets this on every mode
    # switch, so the coach picks up DRAW_DIAGRAM the same way it picks up
    # the answer key, and this initial call is the only other place tools
    # are ever set.
    context.set_tools(session.tools())
    # Session owns the context from here: switch_to_coach() and board.update()
    # only ever change session state, push_context() is the one place that
    # writes it (messages and tools both) into the live LLMContext. See
    # playground/session.py.
    session.context = context
    # Same story for the TTS service: bound here so server.py's session-cap
    # task can re-voice it for the handover without a second OpenAITTSService
    # of its own, and without server.py reaching into this function's locals.
    session.tts = tts

    if kind == "diagnostic":
        llm.register_function("end_round", partial(_end_diagnostic_round, session, on_round_end))
        # No draw_diagram: a diagnostic session never coaches, so nothing may
        # ever call it -- not registering it is the structural half of the
        # tools() guarantee.
    else:
        llm.register_function("end_round", partial(_end_round, session, tts))
        llm.register_function("draw_diagram", partial(_draw_diagram, connection))

    aggregators = LLMContextAggregatorPair(
        context,
        # No vad_analyzer here: LLMUserAggregatorParams(vad_analyzer=...) makes
        # the aggregator build its *own* VADController on the same audio the
        # pipeline's _vad() VADProcessor stage already analyzes -- two Silero
        # instances per session, and the aggregator's controller broadcasts a
        # second VADUserStoppedSpeakingFrame that reaches the upstream
        # SegmentedSTTService (OpenAISTTService) too, which transcribes on
        # every stop frame it sees: one utterance, two billed transcriptions.
        # UserTurnController (which drives SmartTurn) reacts to
        # VADUserStarted/StoppedSpeakingFrame and raw audio regardless of
        # whether the aggregator owns its own VAD controller -- it gets them
        # from whatever reaches process_frame() -- so the pipeline's single
        # _vad() stage is sufficient on its own.
        user_params=LLMUserAggregatorParams(
            # SmartTurn v3's ONNX model ships bundled in the wheel. It is what
            # stops the interviewer cutting in on "...checks the cache first, and".
            user_turn_strategies=UserTurnStrategies(
                stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=LocalSmartTurnAnalyzerV3())]
            ),
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            _vad(config, config.stop_secs),
            stt,
            TranscriptRelay(),
            aggregators.user(),
            llm,
            tts,
            transport.output(),
            aggregators.assistant(),
        ]
    )
    return PipelineWorker(pipeline, params=PipelineParams(enable_metrics=True)), session
