from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .assistant import answer_query, facility_top_item, ranked_facilities
from .data import APP_SCHEMA, FACILITIES_TABLE, NFHS_TABLE, PINCODE_TABLE, DataStore
from .models import (
    AssistantQuery,
    AssistantResponse,
    ShortlistRequest,
    ShortlistResponse,
    TrustCard,
    VerificationRequest,
    VerificationResponse,
    VoiceRequest,
    VoiceResponse,
)
from .scoring import PROCEDURES, score_facility
from .twilio_voice import twilio_voice_entrypoint, twilio_voice_respond
from .voice import SAMPLE_TTS_PATH, build_voice_response, gemini_realtime_status, gemini_sample_audio_path


app = FastAPI(title="CareTrust API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CARESIGNAL_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DataStore()
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "caresignal-backend",
        "app_schema": APP_SCHEMA,
        "data_source": store.last_source,
        "source_tables": {
            "facilities": FACILITIES_TABLE,
            "pincodes": PINCODE_TABLE,
            "nfhs": NFHS_TABLE,
        },
        "procedures": list(PROCEDURES),
    }


@app.get("/api/procedures")
def procedures() -> list[dict[str, object]]:
    return store.list_procedures()


@app.get("/api/facilities/top")
def top_facilities(
    procedure: str = Query("eye_care"),
    country: str | None = Query(None),
    state: str | None = Query(None),
    city: str | None = Query(None),
    pincode: str | None = Query(None),
    age_group: str | None = Query(None),
    limit: int = Query(10, ge=1, le=200),
):
    _validate_procedure(procedure)
    # Age group is accepted for the planner workflow; current source data has no patient-age dimension.
    return ranked_facilities(store, procedure, state, limit, country=country, city=city, pincode=pincode)


@app.get("/api/filters")
def filters() -> dict[str, object]:
    return store.filter_options()


@app.get("/api/service-groupings")
def service_groupings() -> list[dict[str, str]]:
    return store.service_groupings()


@app.get("/api/location-dimensions")
def location_dimensions() -> list[dict[str, object]]:
    return store.location_dimensions()


@app.get("/api/facilities/{unique_id}/trust-card", response_model=TrustCard)
def trust_card(unique_id: str, procedure: str = Query("eye_care")) -> TrustCard:
    _validate_procedure(procedure)
    facility = store.get_facility(unique_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    score = score_facility(facility, procedure)
    source_urls = [url for url in [facility.source_url, facility.website] if url]
    return TrustCard(
        facility=facility,
        procedure=procedure,
        score=score.total_score,
        evidence_snippets=score.evidence_snippets,
        source_urls=source_urls,
        uncertainty_flags=score.uncertainty_flags,
        score_breakdown=score.score_breakdown,
        human_verification_status=facility.human_verification_status,
        human_verification_count=facility.human_verification_count,
        verification_notes=store.verification_notes(unique_id, procedure),
    )


@app.post("/api/verifications", response_model=VerificationResponse)
def verifications(request: VerificationRequest) -> VerificationResponse:
    _validate_procedure(request.procedure)
    facility = store.get_facility(request.unique_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    record = store.add_verification(request)
    updated = facility_top_item(store.get_facility(request.unique_id) or facility, request.procedure)
    return VerificationResponse(ok=True, verification_id=record["verification_id"], facility=updated)


@app.get("/api/verifications/recent")
def recent_verifications(limit: int = Query(20, ge=1, le=100)) -> list[dict[str, object]]:
    return store.recent_verifications(limit)


@app.post("/api/shortlists", response_model=ShortlistResponse)
def shortlists(request: ShortlistRequest) -> ShortlistResponse:
    _validate_procedure(request.procedure)
    if store.get_facility(request.unique_id) is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    record = store.add_shortlist(request)
    return ShortlistResponse(ok=True, shortlist_id=record["shortlist_id"], created_at=record["created_at"])


@app.get("/api/shortlists/recent")
def recent_shortlists(limit: int = Query(20, ge=1, le=100)) -> list[dict[str, object]]:
    return store.recent_shortlists(limit)


@app.post("/api/assistant/query", response_model=AssistantResponse)
def assistant_query(request: AssistantQuery) -> AssistantResponse:
    if request.procedure:
        _validate_procedure(request.procedure)
    return answer_query(store, request)


@app.get("/api/voice/sample")
def voice_sample():
    audio_path = gemini_sample_audio_path()
    if audio_path and audio_path.exists():
        media_type = "audio/wav" if audio_path.suffix.lower() == ".wav" else "audio/ogg"
        return FileResponse(str(audio_path), media_type=media_type, filename=audio_path.name)
    if SAMPLE_TTS_PATH.exists():
        return FileResponse(str(SAMPLE_TTS_PATH), media_type="audio/ogg", filename=SAMPLE_TTS_PATH.name)
    return {"available": False, "message": "Sample TTS file was not found on this machine."}


@app.get("/api/voice/realtime/status")
def voice_realtime_status() -> dict[str, object]:
    return gemini_realtime_status()


@app.post("/api/voice/respond", response_model=VoiceResponse)
def voice_respond(request: VoiceRequest) -> VoiceResponse:
    if request.procedure:
        _validate_procedure(request.procedure)
    return build_voice_response(store, request)


@app.api_route("/api/twilio/voice", methods=["GET", "POST"])
async def twilio_voice(request: Request):
    return await twilio_voice_entrypoint(request)


@app.post("/api/twilio/voice/respond")
async def twilio_voice_turn(request: Request):
    return await twilio_voice_respond(store, request)


@app.get("/")
def root():
    return _frontend_index_response() or health()


@app.get("/{full_path:path}")
def frontend_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    response = _frontend_index_response()
    if response:
        return response
    raise HTTPException(status_code=404, detail="Static frontend is not built; use /api/health.")


def _frontend_index_response() -> FileResponse | None:
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path)) if index_path.exists() else None


def _validate_procedure(procedure: str) -> None:
    if procedure not in PROCEDURES:
        raise HTTPException(status_code=400, detail=f"Unknown procedure '{procedure}'. Use one of: {', '.join(PROCEDURES)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", "8000"))),
        reload=os.getenv("CARESIGNAL_RELOAD", "false").lower() == "true",
    )
