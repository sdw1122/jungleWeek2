BEGIN;

CREATE TABLE IF NOT EXISTS guestbook_replies (
    id BIGSERIAL PRIMARY KEY,
    entry_id BIGINT NOT NULL REFERENCES public_guestbook_entries(id) ON DELETE CASCADE,
    author_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    nickname_snapshot VARCHAR(50) NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_guestbook_replies_content
        CHECK (length(btrim(content)) > 0)
);

CREATE TABLE IF NOT EXISTS guestbook_reactions (
    id BIGSERIAL PRIMARY KEY,
    entry_id BIGINT NOT NULL REFERENCES public_guestbook_entries(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reaction_type VARCHAR(10) NOT NULL,

    CONSTRAINT chk_guestbook_reactions_type
        CHECK (reaction_type IN ('like', 'dislike')),
    CONSTRAINT uq_guestbook_entry_reaction_user
        UNIQUE (entry_id, user_id)
);

CREATE TABLE IF NOT EXISTS guestbook_reply_reactions (
    id BIGSERIAL PRIMARY KEY,
    reply_id BIGINT NOT NULL REFERENCES guestbook_replies(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reaction_type VARCHAR(10) NOT NULL,

    CONSTRAINT chk_guestbook_reply_reactions_type
        CHECK (reaction_type IN ('like', 'dislike')),
    CONSTRAINT uq_guestbook_reply_reaction_user
        UNIQUE (reply_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_guestbook_replies_entry_created
    ON guestbook_replies (entry_id, created_at);

CREATE INDEX IF NOT EXISTS idx_guestbook_reactions_entry
    ON guestbook_reactions (entry_id);

CREATE INDEX IF NOT EXISTS idx_guestbook_reply_reactions_reply
    ON guestbook_reply_reactions (reply_id);

COMMIT;
