-- PostgreSQL master schema: verses, FTS, user profiles, feedback
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS verse_index (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    grantha VARCHAR(128) NOT NULL,
    sthana VARCHAR(128) NOT NULL,
    adhyaya INT NOT NULL,
    shloka INT NOT NULL,
    language VARCHAR(8) DEFAULT 'san',
    metadata JSONB DEFAULT '{}',
    embedding vector(1024),
    fts tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(text, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (grantha, sthana, adhyaya, shloka, language)
);

CREATE INDEX IF NOT EXISTS idx_verse_fts ON verse_index USING GIN (fts);
CREATE INDEX IF NOT EXISTS idx_verse_metadata ON verse_index USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_verse_grantha ON verse_index (grantha, sthana, adhyaya);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prakriti JSONB DEFAULT '{}',
    vikriti JSONB DEFAULT '{}',
    allergies TEXT[] DEFAULT '{}',
    contraindications TEXT[] DEFAULT '{}',
    active_protocol JSONB DEFAULT '{}',
    timeline JSONB DEFAULT '[]',
    efficacy_scores JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interaction_feedback (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(user_id),
    formulation_name VARCHAR(256),
    outcome VARCHAR(32) CHECK (outcome IN ('helped', 'no_effect', 'worsened')),
    checkpoint_day INT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS citation_master (
    id SERIAL PRIMARY KEY,
    grantha VARCHAR(128) NOT NULL,
    sthana VARCHAR(128) NOT NULL,
    adhyaya INT NOT NULL,
    max_shloka INT NOT NULL,
    UNIQUE (grantha, sthana, adhyaya)
);

CREATE OR REPLACE FUNCTION update_profile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_profiles_updated ON user_profiles;
CREATE TRIGGER trg_user_profiles_updated
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_profile_timestamp();
