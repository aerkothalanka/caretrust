CREATE TABLE IF NOT EXISTS public.user_actions (
  action_id UUID PRIMARY KEY,
  user_id VARCHAR,
  facility_id VARCHAR,
  action_type VARCHAR NOT NULL,
  action_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
DECLARE
  constraint_name text;
BEGIN
  SELECT conname INTO constraint_name
  FROM pg_constraint
  WHERE conrelid = 'public.user_actions'::regclass
    AND contype = 'c'
    AND pg_get_constraintdef(oid) LIKE '%action_type%';
  IF constraint_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.user_actions DROP CONSTRAINT %I', constraint_name);
  END IF;
END $$;

ALTER TABLE public.user_actions
  ADD CONSTRAINT user_actions_action_type_check
  CHECK (action_type IN ('note', 'override', 'shortlist', 'review', 'scenario', 'source_verification', 'call_note'));

CREATE INDEX IF NOT EXISTS idx_user_actions_facility_created
  ON public.user_actions (facility_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_actions_type_created
  ON public.user_actions (action_type, created_at DESC);

CREATE TABLE IF NOT EXISTS public.shortlists (
  shortlist_id UUID PRIMARY KEY,
  user_id VARCHAR,
  location VARCHAR,
  service VARCHAR,
  facility_ids VARCHAR[] NOT NULL DEFAULT ARRAY[]::VARCHAR[],
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shortlists_location_service_created
  ON public.shortlists (location, service, created_at DESC);
