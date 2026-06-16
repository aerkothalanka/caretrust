from __future__ import annotations

import html
import asyncio
import re
from urllib.parse import parse_qs, urlencode

from fastapi import Request
from fastapi.responses import Response

from .data import DataStore
from .models import VoiceRequest
from .scoring import PROCEDURES, all_procedure_terms, infer_procedure
from .voice import build_voice_response

TWILIO_CONTENT_TYPE = "application/xml"
VOICE = "alice"
LANGUAGE = "en-IN"


def twiml_response(xml: str) -> Response:
    return Response(content=xml, media_type=TWILIO_CONTENT_TYPE)


async def twilio_voice_entrypoint(request: Request) -> Response:
    """Initial inbound-call webhook. Twilio expects TwiML XML, not JSON."""
    form = await _parse_twilio_form(request)
    call_sid = _field(form, "CallSid") or "caretrust-call"
    action = _public_action_url(request, call_sid)
    prompt = (
        "Welcome to CareTrust, the facility trust desk. "
        "Ask for top facilities, evidence, score breakdown, human verification, or uncertainty. "
        "For example, say: top cardiac surgery facilities, or explain evidence for ACE Heart. "
        "You can also press 1 for cardiac surgery, 2 for eye care, 3 for ICU, or 4 for verification."
    )
    return twiml_response(_gather_twiml(prompt, action))


async def twilio_voice_respond(store: DataStore, request: Request) -> Response:
    """Speech turn webhook. Uses the same deterministic assistant/voice path as the UI voice API."""
    form = await _parse_twilio_form(request)
    session_id = request.query_params.get("session_id") or _field(form, "CallSid") or None
    speech = (_field(form, "SpeechResult") or _digits_to_prompt(_field(form, "Digits")) or "").strip()
    action = _public_action_url(request, session_id or 'caretrust-call')

    if not speech:
        return twiml_response(_gather_twiml("I did not catch that. Please ask about a procedure, facility, evidence, or verification status.", action))
    if _wants_hangup(speech):
        return twiml_response(_say_twiml("Thanks for calling CareTrust. Goodbye.", hangup=True))

    procedure = _infer_procedure(speech)
    facility_id = _resolve_facility_id(store, speech)
    voice_response = await asyncio.to_thread(
        build_voice_response,
        store,
        VoiceRequest(transcript=speech, procedure=procedure, unique_id=facility_id, session_id=session_id),
    )
    spoken = _clean_for_twilio_say(voice_response.text)
    follow_up = " You can ask another question, or say goodbye to end the call."
    return twiml_response(_gather_twiml(f"{spoken}{follow_up}", action))


def _gather_twiml(prompt: str, action: str) -> str:
    hints = ", ".join([str(definition["label"]) for definition in PROCEDURES.values()])
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"<Gather input=\"speech dtmf\" action=\"{action}\" method=\"POST\" speechTimeout=\"auto\" timeout=\"10\" numDigits=\"1\" hints=\"{_xml(hints)}\">"
        f"<Say voice=\"{VOICE}\" language=\"{LANGUAGE}\">{_xml(prompt)}</Say>"
        "</Gather>"
        f"<Say voice=\"{VOICE}\" language=\"{LANGUAGE}\">I did not hear anything. Please call again when you are ready.</Say>"
        "</Response>"
    )


def _say_twiml(prompt: str, *, hangup: bool = False) -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"<Say voice=\"{VOICE}\" language=\"{LANGUAGE}\">{_xml(prompt)}</Say>"
        f"{'<Hangup/>' if hangup else ''}"
        "</Response>"
    )


async def _parse_twilio_form(request: Request) -> dict[str, str]:
    params = {key: value for key, value in request.query_params.items()}
    body = await request.body()
    if not body:
        return params
    parsed = parse_qs(body.decode("utf-8", errors="ignore"), keep_blank_values=True)
    params.update({key: values[-1] if values else "" for key, values in parsed.items()})
    return params


def _field(form: dict[str, str], key: str) -> str | None:
    value = form.get(key)
    return value if value else None


def _public_action_url(request: Request, session_id: str) -> str:
    base = str(request.base_url).rstrip("/")
    query = urlencode({"session_id": session_id})
    return f"{base}/api/twilio/voice/respond?{query}"


def _digits_to_prompt(digits: str | None) -> str | None:
    return {
        "1": "top cardiac surgery facilities",
        "2": "top eye care facilities",
        "3": "top ICU critical care facilities",
        "4": "which cardiac surgery facilities need human verification",
    }.get(digits or "")


def _infer_procedure(question: str) -> str | None:
    return infer_procedure(None, question, default=None)


def _resolve_facility_id(store: DataStore, question: str) -> str | None:
    q = _normalize(question)
    if not q:
        return None
    if _is_broad_facility_query(q):
        return None
    procedure_terms = all_procedure_terms()
    best: tuple[int, str] | None = None
    for facility in store.list_facilities():
        name = _normalize(facility.name)
        if not name:
            continue
        score = 0
        if name in q or q in name:
            score = len(name)
        else:
            tokens = [token for token in name.split() if len(token) >= 3 and token not in procedure_terms]
            overlap = sum(1 for token in tokens if token in q)
            if overlap:
                score = overlap * 10
        if score and (best is None or score > best[0]):
            best = (score, facility.unique_id)
    return best[1] if best and best[0] >= 10 else None


def _is_broad_facility_query(normalized_question: str) -> bool:
    tokens = set(normalized_question.split())
    return bool(tokens & {"top", "best", "rank", "ranked", "ranking", "list", "show", "options"}) and bool(
        tokens & {"facility", "facilities", "hospital", "hospitals", "center", "centers", "centre", "centres"}
    )


def _normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _wants_hangup(speech: str) -> bool:
    q = speech.lower()
    return any(token in q for token in ["goodbye", "bye", "hang up", "end call", "stop call"])


def _clean_for_twilio_say(text: str) -> str:
    cleaned = re.sub(r"[*`#]+", "", text or "")
    cleaned = cleaned.replace("_", " ")
    cleaned = cleaned.replace("/10", " out of 10")
    cleaned = cleaned.replace("/", " out of ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:1350]


def _xml(value: str) -> str:
    return html.escape(value or "", quote=True)
