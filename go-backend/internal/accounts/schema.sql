CREATE TABLE IF NOT EXISTS cat_native_users (
    id bigserial PRIMARY KEY,
    username varchar(150) NOT NULL UNIQUE,
    password_hash text NOT NULL DEFAULT '!',
    email varchar(254) NOT NULL DEFAULT '',
    name varchar(150) NOT NULL DEFAULT '',
    avatar text NOT NULL DEFAULT '',
    active boolean NOT NULL DEFAULT true,
    created timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cat_native_profiles (
    user_id bigint PRIMARY KEY REFERENCES cat_native_users(id) ON DELETE CASCADE,
    birth_year integer,
    consent_completed boolean NOT NULL DEFAULT false,
    consent_version varchar(32) NOT NULL DEFAULT '',
    is_minor boolean NOT NULL DEFAULT false,
    parental_consent_required boolean NOT NULL DEFAULT false,
    display_name varchar(80) NOT NULL DEFAULT '',
    show_on_ranking boolean NOT NULL DEFAULT false,
    created timestamptz NOT NULL DEFAULT now(),
    updated timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cat_native_external (
    provider varchar(16) NOT NULL CHECK (provider IN ('google','facebook')),
    subject varchar(255) NOT NULL,
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    PRIMARY KEY(provider,subject)
);
CREATE TABLE IF NOT EXISTS cat_native_sessions (
    token_hash char(64) PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    expires_at timestamptz NOT NULL,
    created timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS cat_native_sessions_expiry ON cat_native_sessions(expires_at);
CREATE INDEX IF NOT EXISTS cat_native_sessions_user ON cat_native_sessions(user_id,created DESC);
CREATE TABLE IF NOT EXISTS cat_native_oauth_flows (
    state_hash char(64) PRIMARY KEY,
    flow jsonb NOT NULL,
    expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS cat_native_oauth_expiry ON cat_native_oauth_flows(expires_at);
CREATE TABLE IF NOT EXISTS cat_native_auth_attempts (
    key_hash char(64) PRIMARY KEY,
    count integer NOT NULL,
    until timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS cat_native_attempt_expiry ON cat_native_auth_attempts(until);
CREATE TABLE IF NOT EXISTS cat_native_consents (
    id bigserial PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    document varchar(16) NOT NULL CHECK (document IN ('privacy','tos')),
    version varchar(32) NOT NULL,
    text_hash varchar(64) NOT NULL DEFAULT '',
    accepted_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cat_native_scores (
    id bigserial PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    game varchar(20) NOT NULL,
    score integer NOT NULL CHECK(score BETWEEN 0 AND 1000),
    detail varchar(120) NOT NULL,
    at bigint NOT NULL,
    puzzle_key varchar(160) NOT NULL DEFAULT '',
    daily varchar(10) NOT NULL DEFAULT '',
    difficulty varchar(20) NOT NULL DEFAULT '',
    category varchar(40) NOT NULL DEFAULT '',
    created timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id,game,at,puzzle_key)
);
CREATE INDEX IF NOT EXISTS cat_native_scores_user ON cat_native_scores(user_id,at DESC);
CREATE TABLE IF NOT EXISTS cat_native_verified (
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    game varchar(20) NOT NULL CHECK(game IN ('alchimie','intrusul','perechi','conexiuni','contexto','lant')),
    score smallint NOT NULL CHECK(score BETWEEN 0 AND 1000),
    updated timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(user_id,game)
);
CREATE INDEX IF NOT EXISTS cat_native_verified_game ON cat_native_verified(game,score DESC);
CREATE TABLE IF NOT EXISTS cat_native_played (
    user_id bigint NOT NULL REFERENCES cat_native_users(id) ON DELETE CASCADE,
    game varchar(20) NOT NULL,
    pack_id varchar(64) NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(user_id,game,pack_id)
);
CREATE TABLE IF NOT EXISTS cat_native_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());

-- Only digests of opaque game session capabilities are retained. A deleted
-- account becomes an anonymous seal until expiry, never a transferable game.
CREATE TABLE IF NOT EXISTS cat_native_game_owners (
    game varchar(20) NOT NULL CHECK(game IN ('alchimie','intrusul','perechi','conexiuni','contexto','lant')),
    game_hash char(64) NOT NULL,
    user_id bigint REFERENCES cat_native_users(id) ON DELETE SET NULL,
    expires_at timestamptz NOT NULL,
    created timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(game,game_hash)
);
CREATE INDEX IF NOT EXISTS cat_native_game_owners_expiry ON cat_native_game_owners(expires_at);
CREATE INDEX IF NOT EXISTS cat_native_game_owners_user ON cat_native_game_owners(user_id);
