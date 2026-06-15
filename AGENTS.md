# CareSignal build rules

CareSignal is a Databricks Apps hackathon project.

## Stack
- Frontend: React JS + HTML/CSS, simple/elegant, based on docs/design-1-civic-clarity.html.
- Backend: FastAPI Python.
- Databricks query layer: Databricks SQL Statement Execution API where available.
- Persistent app tables: create under `lakebase_hackathon_demo.public`, never `workspace.default`.
- Source dataset tables:
  - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`
  - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory`
  - `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators`

## Product requirements
- Design option 1 is the selected direction: Civic Clarity.
- Scores must be out of 10.0 and explainable.
- Show top 10 facilities grouped by procedure: eye care, cardiac surgery, ICU/critical care, dialysis, oncology, maternity/OBGYN, emergency/trauma.
- Show trust card: evidence snippets, source URLs, uncertainty flags, score breakdown, human verification status.
- Human verification should persist and update rankings.
- Digital call assistant: user calls CareSignal to discuss a facility/procedure ranking and evidence. Include TTS voice support hooks/endpoints.
- Conversational chart assistant: template-based safe answers/charts, not arbitrary SQL in MVP.

## Quality
- Prefer working MVP over broad stubs.
- Include sample/fallback data so local app works without Databricks credentials.
- Do not commit tokens/secrets.
- Run at least syntax/build checks for touched layer.
