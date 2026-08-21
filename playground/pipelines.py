"""Both pipelines. Dictation is the Playground pipeline with the LLM and TTS
stages removed, which is the reason they share a service."""

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
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
from playground.relay import TranscriptRelay
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


DRAW_DIAGRAM = FunctionSchema(
    name="draw_diagram",
    description=(
        "Draw a diagram beside the candidate's work. Give topology only — never "
        "positions, the client lays it out."
    ),
    properties={
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "label": {"type": "string"}},
                "required": ["id", "label"],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["from", "to"],
            },
        },
    },
    required=["nodes", "edges"],
)

END_ROUND = FunctionSchema(
    name="end_round",
    description="End the interview and hand over to the coach.",
    properties={"reason": {"type": "string"}},
    required=["reason"],
)


def build_playground_worker(
    connection: SmallWebRTCConnection, config: VoiceConfig
) -> tuple[PipelineWorker, Session]:
    """mic -> VAD -> STT -> context -> LLM -> TTS -> speaker.

    The interviewer never sees the answer key (playground.personas); the key
    enters the session only when end_round calls session.switch_to_coach().
    """
    session = Session(config)

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
    context.set_tools(ToolsSchema(standard_tools=[END_ROUND, DRAW_DIAGRAM]))
    # Session owns the context from here: switch_to_coach() and board.update()
    # only ever change session state, push_context() is the one place that
    # writes it into the live LLMContext. See playground/session.py.
    session.context = context

    async def on_end_round(params):
        session.switch_to_coach()
        session.push_context()
        # set_voice is deprecated (removed in 2.0.0, TTSUpdateSettingsFrame is
        # the replacement) but still functional in 1.7.0, and this is the only
        # place a voice change is needed -- the audible half of the handoff.
        await tts.set_voice(session.tts_voice())
        await params.result_callback({"ok": True})

    async def on_draw_diagram(params):
        # connection.send_app_message, not transport.output().push_frame:
        # push_frame is meant to be called from inside a FrameProcessor's own
        # process_frame(), not from an arbitrary function-call callback: it
        # gates on the processor already having seen a StartFrame
        # (_check_started) and there's no guarantee of that here. The
        # connection is already in scope, already queues if the data channel
        # isn't open yet, and is what TranscriptRelay's own peer -- the
        # transport's *input* side -- never needed to reach around.
        connection.send_app_message({"type": "draw", "topology": params.arguments})
        await params.result_callback({"drawn": True})

    llm.register_function("end_round", on_end_round)
    llm.register_function("draw_diagram", on_draw_diagram)

    aggregators = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=config.stop_secs, min_volume=config.min_volume)
            ),
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
