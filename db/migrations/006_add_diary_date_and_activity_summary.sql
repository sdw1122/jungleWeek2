BEGIN;

ALTER TABLE diary_entries
    ADD COLUMN IF NOT EXISTS diary_date DATE,
    ADD COLUMN IF NOT EXISTS activity_summary JSONB NOT NULL DEFAULT '{}'::jsonb;

UPDATE diary_entries
SET diary_date = (diary_at AT TIME ZONE 'Asia/Seoul')::date
WHERE diary_date IS NULL;

ALTER TABLE diary_entries
    ALTER COLUMN diary_date SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_diary_plant_date'
          AND conrelid = 'diary_entries'::regclass
    ) THEN
        ALTER TABLE diary_entries
            ADD CONSTRAINT uq_diary_plant_date UNIQUE (plant_id, diary_date);
    END IF;
END;
$$;

COMMIT;
