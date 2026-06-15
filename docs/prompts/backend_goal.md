/goal
You are Codex running the BACKEND/CODING lane for CareSignal with Codex 5.5 high reasoning. Work only inside `/Users/avirkothalanka/caresignal`, primarily `backend/`, `scripts/`, root app deployment files, and backend docs. Do not implement the React UI.

Read:
- AGENTS.md
- docs/IMPLEMENTATION_BRIEF.md

Build a FastAPI backend and Databricks app packaging. Requirements:
1. Create FastAPI app under `backend/` with modules:
   - main.py
   - models.py or schemas.py
   - data.py
   - scoring.py
   - assistant.py
   - voice.py
2. API endpoints:
   - GET /api/health
   - GET /api/procedures
   - GET /api/facilities/top?procedure=eye_care&state=&limit=10
   - GET /api/facilities/{unique_id}/trust-card?procedure=eye_care
   - POST /api/verifications
   - POST /api/shortlists
   - POST /api/assistant/query
   - GET /api/voice/sample
   - POST /api/voice/respond
3. Implement score out of 10.0 using this max allocation:
   - specialties match 1.5
   - procedure match 1.5
   - equipment support 1.0
   - capability support 1.0
   - description support 1.0
   - source URL relevance 1.0
   - phone/website contactability 0.75
   - location completeness 0.5
   - human verification boost 1.5
   - freshness/activity 0.25
   Apply penalties and clamp 0-10. Return score_breakdown and uncertainty_flags.
4. All new tables must be under `lakebase_hackathon_demo.public`. Provide DDL in `scripts/create_lakebase_tables.sql` for:
   - facility_claim_scores
   - facility_human_verifications
   - facility_call_logs
   - planner_shortlists
   - voice_assistant_sessions
   - voice_assistant_turns
5. Databricks source tables:
   - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`
   - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory`
   - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators`
6. Implement Databricks SQL access if env vars/config are present, but include robust local fallback sample data so endpoints work offline.
7. Voice assistant: user calls CareSignal to discuss facility/procedure ranking and evidence. Implement text response generation and serve sample TTS file from `/Users/avirkothalanka/.hermes/profiles/dais2026/audio_cache/tts_20260615_125550.ogg` if present.
8. Conversational chart assistant: safe deterministic intent/template router, not arbitrary SQL. Support top facilities, state comparison, low-confidence claims, facility explanation, verified comparison.
9. Add root `requirements.txt`, `app.yaml`, and backend README/run instructions. FastAPI should serve built frontend from `static/` if present and otherwise return API health at root.
10. Run syntax/import checks using uv or python and report result.

Acceptance criteria:
- `python -m py_compile backend/*.py` succeeds.
- FastAPI app imports successfully.
- Endpoints have fallback data and can be smoke-tested locally if possible.
- Final response should summarize files changed and verification output.
