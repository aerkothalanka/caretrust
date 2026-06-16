# CareSignal Architecture — Baoyu Minimal Variant

Style selection from Baoyu references:
- Type: `framework`
- Style: `minimal`
- Rationale: the Baoyu style guide describes `minimal` as ultra-clean and best for core concepts; this version is intended as a demo-slide alternative with more whitespace and fewer visual elements.

## Narrative
CareSignal converts trusted facility/location data into explainable planner decisions through an agent layer and a Databricks App experience.

## Design constraints
- Exactly three primary architecture blocks.
- No full table names, notebook names, API routes, warehouse IDs, or implementation stack names in the main visual.
- One primary flow only: Data → Agents → Application.
- Secondary feedback is expressed as one small caption, not a crossing arrow.
