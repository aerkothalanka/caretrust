---
type: infographic
style: clean vector architecture diagram
palette: warm orange, teal, blue, purple, green on light background
aspect: 16:9
source: Databricks notebooks + CareSignal app code
---

Create a polished architecture infographic titled "CareTrust / CareSignal Architecture".
Use a left-to-right five-zone flow:
1. Raw / Bronze Sources: Virtue Foundation facilities; India Post pincode directory; NFHS-5 district health indicators.
2. Silver Cleansing: facilities name/address standardization; pincode postal/location normalization.
3. Gold Enrichment: facility trust scoring, service tags, trust tiers, review flags; postal canonicalization and quality flags.
4. Persistence & Sync: Unity Catalog gold Delta tables, Lakebase synced tables, derived app tables for service groups/location dimensions/human verification/shortlists/voice logs.
5. Databricks App: FastAPI backend, deterministic scoring and assistant layer, React frontend tabs, Google Maps radius, trust cards, verification workflow, Gemini/Twilio voice hooks.

Must include exact table names where readable:
- FacilityTrustDesk.virtue_gold.facilities
- FacilityTrustDesk.virtue_gold.india_post_pincode_directory
- lakebase_hackathon_demo.public.facilities_gold_sync
- lakebase_hackathon_demo.public.india_post_pincode_directory_gold_sync

Labels must stay legible and factual. Avoid invented metrics. Include the recorded metrics: 7 service groups; 21,162 deduped location rows from 165,627 India Post rows.
