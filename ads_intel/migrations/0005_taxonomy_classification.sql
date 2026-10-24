CREATE TABLE taxonomy_version (
    version TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
    source TEXT NOT NULL,
    source_hash TEXT,
    definition_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    activated_at TEXT,
    retired_at TEXT
);

CREATE TABLE taxonomy_dimension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy_version TEXT NOT NULL,
    dimension TEXT NOT NULL,
    label TEXT NOT NULL,
    definition TEXT NOT NULL,
    blueprint_section TEXT,
    allows_multiple INTEGER NOT NULL DEFAULT 1 CHECK (allows_multiple IN (0, 1)),
    primary_required INTEGER NOT NULL DEFAULT 0 CHECK (primary_required IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    UNIQUE (taxonomy_version, dimension)
);

CREATE TABLE taxonomy_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy_version TEXT NOT NULL,
    source_dimension TEXT NOT NULL,
    source_tag_key TEXT NOT NULL,
    target_taxonomy_version TEXT,
    target_dimension TEXT,
    target_tag_key TEXT,
    mapping_status TEXT NOT NULL CHECK (mapping_status IN ('mapped', 'needs_review', 'rejected')),
    method TEXT NOT NULL,
    confidence REAL,
    confidence_basis TEXT,
    rationale TEXT,
    evidence_json TEXT,
    created_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    UNIQUE (taxonomy_version, source_dimension, source_tag_key)
);

CREATE TABLE classification_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxonomy_version TEXT NOT NULL,
    run_type TEXT NOT NULL,
    method TEXT NOT NULL,
    model_version TEXT,
    prompt_version TEXT,
    contract_version TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'completed_with_errors', 'failed')),
    counts_json TEXT,
    errors_json TEXT,
    cost_json TEXT,
    notes TEXT
);

ALTER TABLE tag_definition ADD COLUMN taxonomy_version TEXT NOT NULL DEFAULT '1.0.0';

ALTER TABLE ad_tag ADD COLUMN taxonomy_version TEXT NOT NULL DEFAULT '1.0.0';

ALTER TABLE ad_tag ADD COLUMN classification_run_id INTEGER REFERENCES classification_run(id) ON DELETE SET NULL;

ALTER TABLE ad_tag ADD COLUMN legacy_review_status TEXT;

ALTER TABLE ad_tag ADD COLUMN confidence_basis TEXT;

ALTER TABLE ad_tag ADD COLUMN reviewed_by TEXT;

ALTER TABLE ad_tag ADD COLUMN reviewed_at TEXT;

ALTER TABLE ad_tag ADD COLUMN review_notes TEXT;

ALTER TABLE ad_tag ADD COLUMN superseded_by_id INTEGER REFERENCES ad_tag(id) ON DELETE SET NULL;

ALTER TABLE ad_tag ADD COLUMN is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1));

ALTER TABLE ad_tag ADD COLUMN updated_at TEXT;

UPDATE ad_tag
SET legacy_review_status = review_status
WHERE legacy_review_status IS NULL;

UPDATE ad_tag
SET review_status = CASE
        WHEN review_status = 'auto' THEN 'suggested'
        WHEN review_status IN ('imported', 'pending') THEN 'pending_review'
        ELSE review_status
    END
WHERE review_status IN ('auto', 'imported', 'pending');

UPDATE ad_tag
SET updated_at = created_at
WHERE updated_at IS NULL;

UPDATE ad_tag
SET confidence_basis = 'legacy_label_without_numeric_confidence'
WHERE confidence IS NULL AND confidence_basis IS NULL;

UPDATE ad_tag
SET is_primary = 1
WHERE id IN (
    SELECT MIN(t.id)
    FROM ad_tag t
    JOIN tag_definition d ON d.id = t.tag_definition_id
    WHERE d.dimension = 'concepto'
      AND t.review_status IN ('reviewed', 'approved')
    GROUP BY t.ad_creative_id
);

CREATE INDEX ix_ad_tag_review_status ON ad_tag (review_status, taxonomy_version);

CREATE INDEX ix_ad_tag_primary ON ad_tag (ad_creative_id, is_primary, review_status);

CREATE INDEX ix_ad_tag_classification_run ON ad_tag (classification_run_id);

CREATE INDEX ix_taxonomy_mapping_status ON taxonomy_mapping (mapping_status, source_dimension);

CREATE INDEX ix_classification_run_status ON classification_run (status, started_at);

CREATE TABLE ad_tag_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_tag_id INTEGER NOT NULL REFERENCES ad_tag(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    actor TEXT NOT NULL,
    reason TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX ix_ad_tag_event_tag ON ad_tag_event (ad_tag_id, id);
