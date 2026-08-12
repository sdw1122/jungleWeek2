BEGIN;

CREATE TABLE IF NOT EXISTS plant_epithet_fragments (
    id BIGSERIAL PRIMARY KEY,
    slot VARCHAR(10) NOT NULL,
    polarity VARCHAR(10) NOT NULL,
    text VARCHAR(40) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_plant_epithet_fragments_slot
        CHECK (slot IN ('FIRST', 'SECOND')),
    CONSTRAINT chk_plant_epithet_fragments_polarity
        CHECK (polarity IN ('POSITIVE', 'NEGATIVE')),
    CONSTRAINT uq_plant_epithet_fragment
        UNIQUE (slot, polarity, text)
);

INSERT INTO plant_epithet_fragments (slot, polarity, text) VALUES
    ('FIRST', 'POSITIVE', '찬란한'),
    ('FIRST', 'POSITIVE', '축복받은'),
    ('FIRST', 'POSITIVE', '싱그러운'),
    ('FIRST', 'POSITIVE', '다정한'),
    ('FIRST', 'POSITIVE', '눈부신'),
    ('FIRST', 'POSITIVE', '용감한'),
    ('FIRST', 'POSITIVE', '포근한'),
    ('FIRST', 'POSITIVE', '꿈꾸는'),
    ('FIRST', 'POSITIVE', '생명력 넘치는'),
    ('FIRST', 'POSITIVE', '햇살을 머금은'),
    ('FIRST', 'POSITIVE', '별빛에 물든'),
    ('FIRST', 'POSITIVE', '기적을 품은'),
    ('SECOND', 'POSITIVE', '새벽의'),
    ('SECOND', 'POSITIVE', '햇살의'),
    ('SECOND', 'POSITIVE', '별빛의'),
    ('SECOND', 'POSITIVE', '봄바람의'),
    ('SECOND', 'POSITIVE', '푸른 숲의'),
    ('SECOND', 'POSITIVE', '생명의'),
    ('SECOND', 'POSITIVE', '행운의'),
    ('SECOND', 'POSITIVE', '희망의'),
    ('SECOND', 'POSITIVE', '달빛의'),
    ('SECOND', 'POSITIVE', '이슬의'),
    ('SECOND', 'POSITIVE', '정원의'),
    ('SECOND', 'POSITIVE', '무지개의'),
    ('FIRST', 'NEGATIVE', '뒤틀린'),
    ('FIRST', 'NEGATIVE', '저주받은'),
    ('FIRST', 'NEGATIVE', '타락한'),
    ('FIRST', 'NEGATIVE', '메마른'),
    ('FIRST', 'NEGATIVE', '잠식된'),
    ('FIRST', 'NEGATIVE', '폭주하는'),
    ('FIRST', 'NEGATIVE', '음산한'),
    ('FIRST', 'NEGATIVE', '잊혀진'),
    ('FIRST', 'NEGATIVE', '분노한'),
    ('FIRST', 'NEGATIVE', '광기에 젖은'),
    ('FIRST', 'NEGATIVE', '그림자에 물든'),
    ('FIRST', 'NEGATIVE', '종말을 부르는'),
    ('SECOND', 'NEGATIVE', '황천의'),
    ('SECOND', 'NEGATIVE', '심연의'),
    ('SECOND', 'NEGATIVE', '공허의'),
    ('SECOND', 'NEGATIVE', '망각의'),
    ('SECOND', 'NEGATIVE', '광기의'),
    ('SECOND', 'NEGATIVE', '파멸의'),
    ('SECOND', 'NEGATIVE', '어둠의'),
    ('SECOND', 'NEGATIVE', '폐허의'),
    ('SECOND', 'NEGATIVE', '독안개의'),
    ('SECOND', 'NEGATIVE', '붉은 달의'),
    ('SECOND', 'NEGATIVE', '균열의'),
    ('SECOND', 'NEGATIVE', '잿빛 밤의')
ON CONFLICT (slot, polarity, text) DO NOTHING;

ALTER TABLE plants
    ADD COLUMN IF NOT EXISTS epithet_first_id BIGINT,
    ADD COLUMN IF NOT EXISTS epithet_second_id BIGINT;

UPDATE plants SET name = substr(name, length('사랑을 담은') + 2)
WHERE name LIKE '사랑을 담은 %';
UPDATE plants SET name = substr(name, length('행운의') + 2)
WHERE name LIKE '행운의 %';
UPDATE plants SET name = substr(name, length('감사의') + 2)
WHERE name LIKE '감사의 %';
UPDATE plants SET name = substr(name, length('건강을 기원하는') + 2)
WHERE name LIKE '건강을 기원하는 %';
UPDATE plants SET name = substr(name, length('싱그러운') + 2)
WHERE name LIKE '싱그러운 %';
UPDATE plants SET name = substr(name, length('우리의') + 2)
WHERE name LIKE '우리의 %';
UPDATE plants SET name = substr(name, length('존경의') + 2)
WHERE name LIKE '존경의 %';
UPDATE plants SET name = substr(name, length('사랑의') + 2)
WHERE name LIKE '사랑의 %';

UPDATE plants AS plant
SET epithet_first_id = (
    SELECT fragment.id
    FROM plant_epithet_fragments AS fragment
    WHERE fragment.slot = 'FIRST'
      AND fragment.polarity = CASE
          WHEN plant.negative_energy > plant.positive_energy THEN 'NEGATIVE'
          ELSE 'POSITIVE'
      END
      AND fragment.is_active = TRUE
    ORDER BY md5(plant.id::text || ':first:' || fragment.id::text)
    LIMIT 1
)
WHERE plant.epithet_first_id IS NULL;

UPDATE plants AS plant
SET epithet_second_id = (
    SELECT fragment.id
    FROM plant_epithet_fragments AS fragment
    WHERE fragment.slot = 'SECOND'
      AND fragment.polarity = CASE
          WHEN plant.negative_energy > plant.positive_energy THEN 'NEGATIVE'
          ELSE 'POSITIVE'
      END
      AND fragment.is_active = TRUE
    ORDER BY md5(plant.id::text || ':second:' || fragment.id::text)
    LIMIT 1
)
WHERE plant.epithet_second_id IS NULL;

ALTER TABLE plants
    ALTER COLUMN epithet_first_id SET NOT NULL,
    ALTER COLUMN epithet_second_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_plants_epithet_first'
          AND conrelid = 'plants'::regclass
    ) THEN
        ALTER TABLE plants
            ADD CONSTRAINT fk_plants_epithet_first
            FOREIGN KEY (epithet_first_id)
            REFERENCES plant_epithet_fragments(id)
            ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_plants_epithet_second'
          AND conrelid = 'plants'::regclass
    ) THEN
        ALTER TABLE plants
            ADD CONSTRAINT fk_plants_epithet_second
            FOREIGN KEY (epithet_second_id)
            REFERENCES plant_epithet_fragments(id)
            ON DELETE RESTRICT;
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_plant_epithet_fragments_pool
    ON plant_epithet_fragments (polarity, slot, is_active);

COMMIT;
