/goal
You are Claude Code running the FRONTEND lane for CareSignal. Use Opus 4.8 level reasoning. Work only inside `/Users/avirkothalanka/caresignal`, primarily `frontend/` and frontend docs. Do not modify backend implementation except if a tiny type/API contract note is needed.

Read:
- AGENTS.md
- docs/IMPLEMENTATION_BRIEF.md
- docs/design-1-civic-clarity.html

Build a React JS frontend based on Design 1 Civic Clarity. Requirements:
1. Create a Vite React app in `frontend/` if missing.
2. Simple/elegant visual style matching Design 1: dark green left nav, white cards, ranked table, trust card, digital call assistant, chart assistant.
3. Implement components for:
   - Layout
   - ProcedureExplorer
   - FacilityRankingTable
   - TrustCard
   - VerificationForm
   - VoiceAssistantPanel
   - ChartAssistant
4. Frontend calls backend endpoints under `/api/*`, with graceful fallback sample data if API unavailable.
5. Include procedure dropdown: eye care, cardiac surgery, ICU care, dialysis, oncology, maternity/OBGYN, emergency/trauma.
6. Scores are shown out of 10 and include score breakdown in UI.
7. Human verification form posts to `/api/verifications` and immediately updates UI optimistically.
8. Voice assistant panel includes Call CareSignal tel link, Play sample voice button hitting `/api/voice/sample`, and text explanation that user calls CareSignal to discuss rankings/evidence.
9. Chart assistant supports example questions and renders response table/chart from `/api/assistant/query` with fallback.
10. Add frontend README with run/build instructions.
11. Run `npm install` if needed, then `npm run build` and report result.

Acceptance criteria:
- `frontend/package.json` exists.
- `npm run build` succeeds.
- UI can run locally with `npm run dev`.
- Final response should summarize files changed and verification output.
