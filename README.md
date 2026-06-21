# CareSignal

CareSignal is an evidence-backed healthcare facility trust desk built for the Databricks Apps & Agents for Good Hackathon at Data + AI Summit 2026, where the project placed 3rd.

- Live app: https://care-signal.dev
- GitHub repo: https://github.com/aerkothalanka/caretrust
- Built with: Databricks Apps, Lakebase, FastAPI, React, and AI-assisted decision support
- Theme: global health, healthcare access, trust, and practical AI for social impact

## Why we built it

CareSignal was built around Virtue Foundation's global-health mission of delivering care where it is needed most and using data science, AI, and analytics to improve healthcare access in underserved communities.

Finding trusted care can be stressful when facility information is scattered, noisy, incomplete, or hard to compare. CareSignal turns those fragmented signals into a guided decision-support workflow so users can explore care options, review evidence, understand uncertainty, and make more confident decisions.

## What CareSignal does

CareSignal helps users compare healthcare facilities with transparency and human judgment at the center.

Key capabilities:

- Facility discovery by procedure and location
- Trust scoring with explainable score breakdowns
- Evidence snippets and source links for recommendations
- Uncertainty flags where data quality is limited
- Human verification workflow to improve confidence over time
- Conversational chart assistant for safe, template-based insights
- Digital call assistant concept for users who want to ask about facility rankings and verification steps

## Product story

The project started with a simple question:

> How can AI help people make better healthcare decisions when the data is scattered, noisy, and hard to trust?

Instead of building a generic chatbot, CareSignal focuses on a practical workflow. Users can search facilities, inspect why a recommendation was made, see where the evidence is strong or weak, and add human verification back into the system.

The goal is not to replace expert or family judgment. The goal is to make care discovery clearer, faster, and more trustworthy.

## Architecture

CareSignal combines:

- **React and Vite frontend** for the interactive dashboard
- **FastAPI backend** for ranked facility discovery, trust cards, verification, chart assistant, and voice-assistant hooks
- **Databricks Apps** for deployment
- **Lakebase** for fast operational data access and persistent app state
- **Unity Catalog / Databricks datasets** for healthcare facility and public-health data
- **AI-assisted workflows** for grounded decision support, not automated decision-making

Databricks source datasets used by the app include:

```text
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory
databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators
```

## Local development

### Backend

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

The backend includes fallback sample data, so it can run locally without Databricks credentials.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

For a production build:

```bash
cd frontend
npm run build
```

## Databricks configuration

When available, the backend can read from Databricks using:

```text
DATABRICKS_HOST
DATABRICKS_TOKEN
DATABRICKS_WAREHOUSE_ID
```

For Lakebase/Postgres-backed persistence, configure:

```text
PGHOST
PGDATABASE
PGUSER
PGPASSWORD
```

If these are not present, the app keeps demo state in process memory for local use.

## Repository structure

```text
backend/                 FastAPI application and data layer
frontend/                React/Vite frontend
static/                  Built static assets for deployment
docs/                    Design and implementation notes
scripts/                 Lakebase and setup scripts
artifacts/               Demo, pitch, and architecture assets
app.yaml                 Databricks App configuration
```

## Smoke checks

```bash
python -m py_compile backend/*.py
python -c "from backend.main import app; print(app.title)"
```

Useful local API checks:

```bash
curl http://localhost:8000/api/procedures
curl "http://localhost:8000/api/facilities/top?procedure=eye_care&limit=3"
curl "http://localhost:8000/api/facilities/fallback-aravind-madurai/trust-card?procedure=eye_care"
```

## Team and acknowledgements

Built by Rishi Kothalanka and Neelima Talasila during the Databricks Apps & Agents for Good Hackathon.

Thanks to Databricks, OpenAI, Virtue Foundation, the hackathon team, mentors, judges, and the Data + AI Summit builder community for creating a great environment to build practical AI for social impact.

## License

Add the appropriate open-source license for reuse and contribution terms.
