from __future__ import annotations

from pathlib import Path

from .assistant import answer_query
from .data import DataStore
from .models import AssistantQuery, VoiceRequest, VoiceResponse


SAMPLE_TTS_PATH = Path("/Users/avirkothalanka/.hermes/profiles/dais2026/audio_cache/tts_20260615_125550.ogg")


def build_voice_response(store: DataStore, request: VoiceRequest) -> VoiceResponse:
    session_id = store.start_or_get_voice_session(request.session_id)
    assistant_response = answer_query(
        store,
        AssistantQuery(
            question=request.transcript,
            procedure=request.procedure,
            unique_id=request.unique_id,
        ),
    )
    text = (
        f"CareSignal summary: {assistant_response.answer} "
        "For a live referral, confirm department availability, appointment timing, costs, and emergency readiness."
    )
    logged = store.log_voice_turn(session_id, request, text, assistant_response.intent)
    store.log_call(session_id, request.unique_id, request.procedure, text[:500])
    return VoiceResponse(
        session_id=session_id,
        text=text,
        audio_url="/api/voice/sample" if SAMPLE_TTS_PATH.exists() else None,
        intent=assistant_response.intent,
        logged=logged,
    )
