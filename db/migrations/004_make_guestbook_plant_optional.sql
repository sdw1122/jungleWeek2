BEGIN;

-- Public guestbook entries are no longer tied to a specific plant.
-- Keep the legacy column for existing data, but allow current inserts
-- that only provide the author and message fields.
ALTER TABLE public_guestbook_entries
    ALTER COLUMN plant_id DROP NOT NULL;

COMMIT;
