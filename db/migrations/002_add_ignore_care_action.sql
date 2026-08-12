BEGIN;

ALTER TABLE care_logs
    DROP CONSTRAINT IF EXISTS chk_care_logs_action_type;

ALTER TABLE care_logs
    ADD CONSTRAINT chk_care_logs_action_type
    CHECK (action_type IN ('PRAISE', 'PET', 'WATER', 'SUNLIGHT', 'IGNORE'));

COMMIT;
