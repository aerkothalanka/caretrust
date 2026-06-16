# CareSignal Architecture — Executive Demo Slide

This version is intentionally simplified for a hackathon demo/judging panel. The diagram removes implementation-level detail and presents three conceptual layers only.

## Narrative
**Trusted healthcare data → explainable facility agents → planner-facing Databricks App**

## Layers shown
- **Data Layer**: raw facility/location/public health sources are cleansed, enriched, and persisted as app-ready Gold/Lakebase data products.
- **Agent Layer**: trust scoring, planner assistant, voice handoff, and human verification turn data into explainable decisions.
- **Application Layer**: Databricks App experience exposes ranked facilities, maps, Trust Cards, verification, chat, and phone workflows.

## Design choices
- Three large executive cards instead of many technical boxes.
- One primary left-to-right flow line, no crossing arrows.
- Implementation details live in notes/source code, not the slide.
- Professional neutral background, restrained Databricks orange + healthcare teal accents, strong whitespace.
