BEGIN;

DROP TABLE IF EXISTS diary_media;

DROP INDEX IF EXISTS uq_gifts_claim_code_hash;
ALTER TABLE gifts
    DROP COLUMN IF EXISTS claim_code_hash;

DROP INDEX IF EXISTS idx_public_diary;
ALTER TABLE diary_entries
    DROP COLUMN IF EXISTS is_public;

DELETE FROM care_logs
WHERE action_type = 'PRAISE';

ALTER TABLE care_logs
    DROP CONSTRAINT IF EXISTS chk_care_logs_action_type;

ALTER TABLE care_logs
    ADD CONSTRAINT chk_care_logs_action_type
    CHECK (action_type IN ('PET', 'WATER', 'SUNLIGHT', 'IGNORE'));

COMMIT;
