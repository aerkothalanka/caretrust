# /goal CareSignal implementation brief

Build CareSignal: an evidence-backed healthcare facility trust desk for the Databricks hackathon.

Selected frontend direction: `docs/design-1-civic-clarity.html`.

## Must-have MVP
1. React frontend implementing Design 1 style: left nav, procedure explorer, ranked top-10 table, trust card, digital call assistant panel, chart assistant panel.
2. FastAPI backend exposing:
   - `GET /api/health`
   - `GET /api/procedures`
   - `GET /api/facilities/top?procedure=eye_care&state=&limit=10`
   - `GET /api/facilities/{unique_id}/trust-card?procedure=eye_care`
   - `POST /api/verifications`
   - `POST /api/shortlists`
   - `POST /api/assistant/query`
   - `GET /api/voice/sample`
   - `POST /api/voice/respond`
3. Score model out of 10:
   - specialties match: 1.5
   - procedure match: 1.5
   - equipment support: 1.0
   - capability support: 1.0
   - description support: 1.0
   - source URL relevance: 1.0
   - phone/website contactability: 0.75
   - location completeness: 0.5
   - human verification boost: 1.5
   - freshness/activity: 0.25
   - penalties for noisy/mismatched/missing/disproved; clamp 0-10.
4. Tables under `lakebase_hackathon_demo.public`:
   - `facility_claim_scores`
   - `facility_human_verifications`
   - `facility_call_logs`
   - `planner_shortlists`
   - `voice_assistant_sessions`
   - `voice_assistant_turns`
5. Databricks app packaging: `app.yaml`, `requirements.txt`, FastAPI serves built React static assets.
6. Local fallback sample data so demo works if Databricks auth is unavailable.

## Voice assistant behavior
The user calls CareSignal, not necessarily the facility. It should answer questions like:
- Why is Aravind Eye Hospital ranked 6.8 for eye care?
- What evidence supports Fortis for cardiac surgery?
- What should I verify when I call/visit this hospital?

TTS sample already exists at `/Users/avirkothalanka/.hermes/profiles/dais2026/audio_cache/tts_20260615_125550.ogg`; implement hooks that can serve a sample audio if present and return text responses otherwise.

## Demo story
Search procedure -> view top facilities -> inspect trust card -> ask assistant -> call CareSignal / play voice sample -> submit human verification -> ranking improves.
