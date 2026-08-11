BEGIN;

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    auth_provider VARCHAR(20) NOT NULL DEFAULT 'LOCAL',
    google_subject VARCHAR(255) UNIQUE,
    nickname VARCHAR(50) NOT NULL UNIQUE,
    profile_image_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_users_auth_provider
        CHECK (auth_provider IN ('LOCAL', 'GOOGLE')),
    CONSTRAINT chk_users_auth_credentials
        CHECK (
            (auth_provider = 'LOCAL' AND password_hash IS NOT NULL AND google_subject IS NULL)
            OR
            (auth_provider = 'GOOGLE' AND google_subject IS NOT NULL)
        ),
    CONSTRAINT chk_users_status
        CHECK (status IN ('ACTIVE', 'WITHDRAWN'))
);

CREATE TABLE plant_species (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(30),
    emoji VARCHAR(16),
    image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE plants (
    id BIGSERIAL PRIMARY KEY,
    species_id BIGINT NOT NULL REFERENCES plant_species(id) ON DELETE RESTRICT,
    name VARCHAR(50) NOT NULL,
    growth_score SMALLINT NOT NULL DEFAULT 0,
    positive_energy INTEGER NOT NULL DEFAULT 0,
    negative_energy INTEGER NOT NULL DEFAULT 0,
    mood VARCHAR(30),
    status VARCHAR(20) NOT NULL DEFAULT 'GROWING',
    adopted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_plants_growth_score
        CHECK (growth_score BETWEEN 0 AND 100),
    CONSTRAINT chk_plants_positive_energy
        CHECK (positive_energy >= 0),
    CONSTRAINT chk_plants_negative_energy
        CHECK (negative_energy >= 0),
    CONSTRAINT chk_plants_status
        CHECK (status IN ('GROWING', 'GIFT_READY', 'GIFTED'))
);

CREATE TABLE gifts (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    sender_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    recipient_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    recipient_name VARCHAR(50) NOT NULL,
    gifted_on DATE NOT NULL,
    message_card TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'READY',
    claim_code_hash VARCHAR(255),
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_gifts_status
        CHECK (status IN ('READY', 'SENT', 'ACCEPTED', 'CANCELLED')),
    CONSTRAINT chk_gifts_acceptance
        CHECK (
            (status = 'ACCEPTED' AND accepted_at IS NOT NULL)
            OR
            (status <> 'ACCEPTED' AND accepted_at IS NULL)
        )
);

CREATE TABLE plant_ownerships (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    owner_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    acquisition_type VARCHAR(20) NOT NULL,
    gift_id BIGINT REFERENCES gifts(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,

    CONSTRAINT chk_plant_ownerships_acquisition_type
        CHECK (acquisition_type IN ('ADOPTION', 'GIFT')),
    CONSTRAINT chk_plant_ownerships_gift
        CHECK (
            (acquisition_type = 'ADOPTION' AND gift_id IS NULL)
            OR
            (acquisition_type = 'GIFT' AND gift_id IS NOT NULL)
        ),
    CONSTRAINT chk_plant_ownerships_period
        CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE TABLE care_logs (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action_type VARCHAR(30) NOT NULL,
    growth_delta SMALLINT NOT NULL DEFAULT 0,
    positive_delta INTEGER NOT NULL DEFAULT 0,
    negative_delta INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_care_logs_action_type
        CHECK (action_type IN ('PET', 'WATER', 'SUNLIGHT', 'IGNORE'))
);

CREATE TABLE chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,

    CONSTRAINT chk_chat_sessions_period
        CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    positive_delta INTEGER NOT NULL DEFAULT 0,
    negative_delta INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_chat_messages_role
        CHECK (role IN ('USER', 'PLANT', 'SYSTEM'))
);

CREATE TABLE diary_entries (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    author_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(150),
    content TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    mood_snapshot VARCHAR(30),
    growth_score_snapshot SMALLINT NOT NULL,
    positive_energy_snapshot INTEGER NOT NULL,
    negative_energy_snapshot INTEGER NOT NULL,
    growth_stage_snapshot VARCHAR(20) NOT NULL,
    growth_tendency_snapshot VARCHAR(20) NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    diary_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_diary_entries_source_type
        CHECK (source_type IN ('USER', 'AI')),
    CONSTRAINT chk_diary_growth_score
        CHECK (growth_score_snapshot BETWEEN 0 AND 100),
    CONSTRAINT chk_diary_positive_energy
        CHECK (positive_energy_snapshot >= 0),
    CONSTRAINT chk_diary_negative_energy
        CHECK (negative_energy_snapshot >= 0),
    CONSTRAINT chk_diary_growth_stage
        CHECK (growth_stage_snapshot IN ('SEED', 'COTYLEDON', 'TRUE_LEAF', 'BUD', 'FLOWER')),
    CONSTRAINT chk_diary_growth_tendency
        CHECK (growth_tendency_snapshot IN ('POSITIVE', 'NEGATIVE'))
);

CREATE TABLE diary_media (
    id BIGSERIAL PRIMARY KEY,
    diary_entry_id BIGINT NOT NULL REFERENCES diary_entries(id) ON DELETE CASCADE,
    media_type VARCHAR(20) NOT NULL,
    media_url TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_diary_media_type
        CHECK (media_type IN ('IMAGE', 'VIDEO')),
    CONSTRAINT chk_diary_media_sort_order
        CHECK (sort_order >= 0),
    CONSTRAINT uq_diary_media_sort_order
        UNIQUE (diary_entry_id, sort_order)
);

CREATE TABLE public_guestbook_entries (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE RESTRICT,
    author_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    nickname_snapshot VARCHAR(50) NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_public_guestbook_content
        CHECK (length(btrim(content)) > 0)
);

CREATE UNIQUE INDEX uq_active_plant_owner
    ON plant_ownerships (plant_id)
    WHERE ended_at IS NULL;

CREATE UNIQUE INDEX uq_ownership_gift
    ON plant_ownerships (gift_id)
    WHERE gift_id IS NOT NULL;

CREATE UNIQUE INDEX uq_gifts_claim_code_hash
    ON gifts (claim_code_hash)
    WHERE claim_code_hash IS NOT NULL;

CREATE INDEX idx_plants_species
    ON plants (species_id);

CREATE INDEX idx_ownerships_owner_active
    ON plant_ownerships (owner_user_id, ended_at);

CREATE INDEX idx_care_logs_plant_created
    ON care_logs (plant_id, created_at DESC);

CREATE INDEX idx_chat_sessions_plant
    ON chat_sessions (plant_id, started_at DESC);

CREATE INDEX idx_chat_messages_session
    ON chat_messages (session_id, created_at);

CREATE INDEX idx_diary_entries_plant_date
    ON diary_entries (plant_id, diary_at DESC);

CREATE INDEX idx_public_diary
    ON diary_entries (diary_at DESC)
    WHERE is_public = TRUE;

CREATE INDEX idx_guestbook_plant_created
    ON public_guestbook_entries (plant_id, created_at DESC);

CREATE INDEX idx_gifts_recipient
    ON gifts (recipient_user_id, gifted_on DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_plant_species_updated_at
    BEFORE UPDATE ON plant_species
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_plants_updated_at
    BEFORE UPDATE ON plants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_gifts_updated_at
    BEFORE UPDATE ON gifts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_diary_entries_updated_at
    BEFORE UPDATE ON diary_entries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_public_guestbook_entries_updated_at
    BEFORE UPDATE ON public_guestbook_entries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
