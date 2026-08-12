BEGIN;

ALTER TABLE plant_species
    ADD COLUMN IF NOT EXISTS name VARCHAR(50),
    ADD COLUMN IF NOT EXISTS category VARCHAR(30),
    ADD COLUMN IF NOT EXISTS emoji VARCHAR(16);

UPDATE plant_species
SET name = 'species-' || id
WHERE name IS NULL OR btrim(name) = '';

ALTER TABLE plant_species
    ALTER COLUMN name SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_plant_species_name'
          AND conrelid = 'plant_species'::regclass
    ) THEN
        ALTER TABLE plant_species
            ADD CONSTRAINT uq_plant_species_name UNIQUE (name);
    END IF;
END;
$$;

COMMIT;
