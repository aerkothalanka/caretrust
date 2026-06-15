from __future__ import annotations

import asyncio
import os
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

from .assistant import answer_query
from .data import DataStore
from .models import AssistantQuery, VoiceRequest, VoiceResponse


SAMPLE_TTS_PATH = Path("/Users/avirkothalanka/.hermes/profiles/dais2026/audio_cache/tts_20260615_125550.ogg")
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview")
GEMINI_LIVE_VOICE = os.getenv("GEMINI_LIVE_VOICE", "Puck")
GEMINI_TIMEOUT_SECONDS = float(os.getenv("GEMINI_LIVE_TIMEOUT_SECONDS", "14"))
GEMINI_SAMPLE_WAV = Path(tempfile.gettempdir()) / "caresignal_gemini_live_sample.wav"


@dataclass
class GeminiLiveResult:
    text: str | None = None
    audio_path: Path | None = None
    error: str | None = None


def gemini_realtime_status() -> dict[str, object]:
    """Return non-sensitive Gemini Live configuration status for UI/API probes."""
    return {
        "provider": "gemini-live",
        "enabled": bool(os.getenv("GEMINI_API_KEY")),
        "model": GEMINI_LIVE_MODEL,
        "voice": GEMINI_LIVE_VOICE,
        "response_modalities": ["AUDIO", "TEXT"],
        "transport": "Gemini Live API via Google GenAI SDK",
    }


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
    deterministic_text = (
        f"CareSignal summary: {assistant_response.answer} "
        "For a live referral, confirm department availability, appointment timing, costs, and emergency readiness."
    )
    prompt = _voice_prompt(request.transcript, deterministic_text)
    gemini_result = _run_gemini_live_text(prompt) if os.getenv("GEMINI_API_KEY") else GeminiLiveResult()
    text = gemini_result.text or deterministic_text
    provider = "gemini-live" if gemini_result.text else "deterministic-fallback"
    logged = store.log_voice_turn(session_id, request, text, assistant_response.intent)
    store.log_call(session_id, request.unique_id, request.procedure, text[:500])
    return VoiceResponse(
        session_id=session_id,
        text=text,
        audio_url="/api/voice/sample",
        intent=assistant_response.intent,
        logged=logged,
        provider=provider,
        realtime_model=GEMINI_LIVE_MODEL if os.getenv("GEMINI_API_KEY") else None,
        realtime_error=gemini_result.error,
    )


def gemini_sample_audio_path() -> Path | None:
    """Generate/cache a short Gemini Live audio sample when configured; fallback to static TTS."""
    if not os.getenv("GEMINI_API_KEY"):
        return SAMPLE_TTS_PATH if SAMPLE_TTS_PATH.exists() else None
    if GEMINI_SAMPLE_WAV.exists() and GEMINI_SAMPLE_WAV.stat().st_size > 44:
        return GEMINI_SAMPLE_WAV
    prompt = (
        "You are CareSignal's Facility Trust Desk voice assistant. In one brief sentence, "
        "say that you can explain facility rankings, evidence, uncertainty, and verification steps."
    )
    result = _run_gemini_live_audio(prompt)
    if result.audio_path and result.audio_path.exists():
        return result.audio_path
    return SAMPLE_TTS_PATH if SAMPLE_TTS_PATH.exists() else None


def _voice_prompt(user_transcript: str, deterministic_context: str) -> str:
    return (
        "You are CareSignal's realtime voice assistant for healthcare facility planners. "
        "Answer conversationally in 2-3 short sentences. Explain rankings, evidence, uncertainty, "
        "and human verification steps. Do not provide medical advice; focus on facility capability evidence.\n\n"
        f"User said: {user_transcript}\n"
        f"CareSignal context: {deterministic_context}"
    )


def _run_gemini_live_text(prompt: str) -> GeminiLiveResult:
    try:
        return asyncio.run(_gemini_live_turn(prompt, audio=False))
    except Exception as exc:  # pragma: no cover - protects demo fallback when API/key/model is unavailable.
        return GeminiLiveResult(error=_safe_error(exc))


def _run_gemini_live_audio(prompt: str) -> GeminiLiveResult:
    try:
        return asyncio.run(_gemini_live_turn(prompt, audio=True))
    except Exception as exc:  # pragma: no cover
        return GeminiLiveResult(error=_safe_error(exc))


async def _gemini_live_turn(prompt: str, *, audio: bool) -> GeminiLiveResult:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:  # pragma: no cover
        return GeminiLiveResult(error=f"google-genai unavailable: {type(exc).__name__}")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return GeminiLiveResult(error="GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)
    config_kwargs: dict[str, object] = {
        "response_modalities": [types.Modality.AUDIO if audio else types.Modality.TEXT],
        "system_instruction": types.Content(
            parts=[
                types.Part(
                    text=(
                        "You are CareSignal, a concise, calm facility trust desk voice assistant. "
                        "Use evidence-grounded language and remind users to verify live availability."
                    )
                )
            ]
        ),
    }
    if audio:
        config_kwargs.update(
            {
                "speech_config": types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_LIVE_VOICE)
                    )
                ),
                "output_audio_transcription": types.AudioTranscriptionConfig(),
            }
        )
    config = types.LiveConnectConfig(**config_kwargs)

    text_chunks: list[str] = []
    audio_chunks: list[bytes] = []

    async with asyncio.timeout(GEMINI_TIMEOUT_SECONDS):
        async with client.aio.live.connect(model=GEMINI_LIVE_MODEL, config=config) as session:
            await session.send_realtime_input(text=prompt)
            async for response in session.receive():
                if getattr(response, "text", None):
                    text_chunks.append(response.text)
                server_content = getattr(response, "server_content", None)
                if server_content:
                    if getattr(server_content, "output_transcription", None) and server_content.output_transcription.text:
                        text_chunks.append(server_content.output_transcription.text)
                    model_turn = getattr(server_content, "model_turn", None)
                    if model_turn and getattr(model_turn, "parts", None):
                        for part in model_turn.parts:
                            inline_data = getattr(part, "inline_data", None)
                            if inline_data and getattr(inline_data, "data", None):
                                audio_chunks.append(inline_data.data)
                    if getattr(server_content, "turn_complete", False):
                        break

    audio_path = None
    if audio and audio_chunks:
        audio_path = GEMINI_SAMPLE_WAV
        _write_pcm24k_wav(audio_path, b"".join(audio_chunks))
    return GeminiLiveResult(text="".join(text_chunks).strip() or None, audio_path=audio_path)


def _write_pcm24k_wav(path: Path, pcm_bytes: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(pcm_bytes)


def _safe_error(exc: Exception) -> str:
    message = str(exc).replace(os.getenv("GEMINI_API_KEY", "__NO_KEY__"), "[REDACTED]")
    return f"{type(exc).__name__}: {message[:220]}"
