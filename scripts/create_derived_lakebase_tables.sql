-- CareSignal Lakebase/Postgres derived tables created from hackathon source tables.
-- Run against Lakebase Postgres database `publicdata` on project `hackathon-demo`.

CREATE TABLE IF NOT EXISTS caresignal_service_specialty_groups (
  service_id text PRIMARY KEY,
  service_label text NOT NULL,
  specialty_group text NOT NULL,
  keywords text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS caresignal_location_dimension (
  country text NOT NULL,
  state text,
  city text,
  postal_code text,
  latitude double precision,
  longitude double precision,
  source_table text,
  PRIMARY KEY(country, state, city, postal_code)
);

-- Populated on 2026-06-15 from:
-- databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory
-- Result counts from execution:
--   caresignal_service_specialty_groups: 7 rows
--   caresignal_location_dimension: 21,162 deduped country/state/city/postal-code rows from 165,627 India Post rows
