# CareSignal Backend

FastAPI backend for the CareSignal Databricks Apps hackathon project. It serves API endpoints for ranked facility discovery, trust cards, human verification, deterministic chart-assistant responses, and voice-assistant text/TTS hooks.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.main
```

Then open:

```text
http://localhost:8000/api/health
http://localhost:8000/docs
```

The backend works without Databricks credentials by using bundled fallback facilities.

## Databricks Configuration

When these are present, the data layer attempts Databricks SQL reads from the Statement Execution API first (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_WAREHOUSE_ID`), then the Databricks SQL connector with SDK `Config()`:

```text
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators
```

Required app resources are declared in `app.yaml` with `valueFrom`:

- `DATABRICKS_WAREHOUSE_ID` from a SQL warehouse resource.
- `DB_CONNECTION_STRING` from a Lakebase database resource.

Lakebase/Postgres writes are attempted only when `PGHOST`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD` are injected. Otherwise verifications, shortlists, and voice turns are kept in process memory for local demo use.

## Tables

Run `scripts/create_lakebase_tables.sql` in Databricks SQL to create persistent app tables under `lakebase_hackathon_demo.public`.

## Smoke Tests

```bash
python -m py_compile backend/*.py
python -c "from backend.main import app; print(app.title)"
```

Useful API checks:

```bash
curl http://localhost:8000/api/procedures
curl "http://localhost:8000/api/facilities/top?procedure=eye_care&limit=3"
curl "http://localhost:8000/api/facilities/fallback-aravind-madurai/trust-card?procedure=eye_care"
```
