CREATE SCHEMA IF NOT EXISTS lakebase_hackathon_demo.public;

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.facility_claim_scores (
  claim_score_id STRING NOT NULL,
  facility_unique_id STRING NOT NULL,
  procedure STRING NOT NULL,
  total_score DOUBLE NOT NULL,
  score_breakdown_json STRING NOT NULL,
  uncertainty_flags_json STRING NOT NULL,
  evidence_snippets_json STRING NOT NULL,
  score_version STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.facility_human_verifications (
  verification_id STRING NOT NULL,
  facility_unique_id STRING NOT NULL,
  procedure STRING NOT NULL,
  verification_status STRING NOT NULL,
  verifier_name STRING,
  notes STRING,
  evidence_url STRING,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.facility_call_logs (
  call_id STRING NOT NULL,
  session_id STRING,
  facility_unique_id STRING,
  procedure STRING,
  call_summary STRING,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.planner_shortlists (
  shortlist_id STRING NOT NULL,
  facility_unique_id STRING NOT NULL,
  procedure STRING NOT NULL,
  planner_name STRING,
  notes STRING,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.voice_assistant_sessions (
  session_id STRING NOT NULL,
  caller_id STRING,
  created_at TIMESTAMP NOT NULL,
  last_turn_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lakebase_hackathon_demo.public.voice_assistant_turns (
  turn_id STRING NOT NULL,
  session_id STRING NOT NULL,
  facility_unique_id STRING,
  procedure STRING,
  caller_transcript STRING NOT NULL,
  assistant_response STRING NOT NULL,
  intent STRING,
  created_at TIMESTAMP NOT NULL
);
