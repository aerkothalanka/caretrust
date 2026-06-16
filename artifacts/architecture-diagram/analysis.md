# CareSignal Demo Architecture — Refined

This version intentionally removes implementation-level detail from the original architecture diagram so it is suitable for a hackathon demo slide.

## Source grounding
- Databricks workspace notebooks define the raw → cleansed → enriched data flow for healthcare facilities and India Post location data.
- The CareSignal app code defines a Databricks App with FastAPI backend, React frontend, explainable scoring, assistant endpoints, verification, shortlists, map/radius views, and voice hooks.

## Demo narrative
1. **Data Layer** turns raw facility, location, and health-context sources into trusted app-ready records.
2. **Agent Layer** converts those records into explainable rankings, answers, voice guidance, and human verification loops.
3. **Application Layer** presents the workflow as a Databricks App for planners: explore, map, inspect trust cards, verify claims, shortlist, and ask questions.

## Refinement notes from Claude Code review
- Use three swim lanes instead of the previous dense five-column pipeline.
- Remove full table paths, notebook filenames, API routes, warehouse IDs, and debug footnotes.
- Reduce card count and arrows.
- Group trust logic into a few high-level concepts instead of many pills.
- Use a clean neutral background and demo-ready typography.
