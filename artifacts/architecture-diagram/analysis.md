# CareSignal / CareTrust Architecture Analysis

Source inspected:
- Databricks workspace folder `/Workspace/Users/nilima.talasila@gmail.com` exported from object id `2586464831214979`.
- Local app code under `/Users/avirkothalanka/caresignal`.

Raw / bronze sources:
- `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`
- `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory`
- `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators` (referenced by app as a future/public health context source)

Silver cleansing:
- `facilities_bronze_to_silver.py`: standardizes facility names, removes junk descriptive rows, preserves acronyms, normalizes city/state/postcode fields.
- `india_post_pincode_directory_bronze_to_silver.py`: text cleanup, valid 6-digit pincode checks, normalized office/district/state values, known district/city fixes including Kaimur/Bhabua and North/South 24 Parganas.

Gold enrichment:
- `facilities_silver_to_gold.py`: strips trailing address fragments from names, extracts service tags, computes core identity/contact/location/evidence/service signal scores, derives `facility_trust_score`, `trust_tier`, `review_flag`, `primary_service_tag`, and `source_text_blob`.
- `india_post_pincode_directory_silver_to_gold.py`: creates canonical district/state/city/office variants, parses pincode/lat/lon, validates geographic fields, and writes `needs_review` plus `gold_quality_notes`.

Persistence / sync:
- Gold Delta tables are persisted in `FacilityTrustDesk.virtue_gold.*`.
- The Databricks App reads synced Lakebase/Postgres tables under `lakebase_hackathon_demo.public`: `facilities_gold_sync`, `india_post_pincode_directory_gold_sync`.
- Derived app tables include service groupings, location dimensions, verification records, planner shortlists, voice sessions/turns, and call logs.

App architecture:
- Databricks App command: `python -m backend.main`.
- Backend: FastAPI (`backend/main.py`) serving API routes and static React build.
- Data access: Databricks SQL Statement Execution API for UC/Lakebase-synced tables; psycopg2 for Lakebase inserts/reads when PG env vars are present; fallback sample data for local/demo resilience.
- Scoring: deterministic score out of 10.0 using specialties, procedure, equipment, capability, description, source URL, contactability, location completeness, human verification, freshness, and uncertainty penalties.
- Frontend: React with tabs Explorer, Map + Radius, Verification, Chat Assistant; filters for country/state/city/postal code/service/focus/radius; trust cards, map radius, verification workflow, shortlists, assistant answers.
- Voice/agent surface: template-safe chat assistant; Gemini Live status/sample voice hooks; Twilio webhook endpoints for phone assistant.

Note: attempted live Databricks SQL row count query, but warehouse start was blocked by free daily limit. Diagram uses row counts only where the checked-in SQL script records them: 165,627 India Post rows -> 21,162 deduped location rows, and 7 service groups.
