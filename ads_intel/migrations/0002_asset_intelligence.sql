ALTER TABLE source ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE source ADD COLUMN permission_evidence_ref TEXT;
ALTER TABLE source ADD COLUMN permission_reviewer TEXT;
ALTER TABLE source ADD COLUMN permission_reviewed_at TEXT;
ALTER TABLE asset ADD COLUMN rights_evidence_ref TEXT;
ALTER TABLE asset ADD COLUMN rights_reviewer TEXT;
ALTER TABLE asset ADD COLUMN rights_reviewed_at TEXT;

CREATE TABLE review_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    review_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_review', 'approved', 'restricted', 'rejected', 'needs_evidence', 'resolved')),
    evidence_ref TEXT,
    reviewer TEXT,
    reviewed_at TEXT,
    notes TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX ix_review_event_object ON review_event (object_type, object_id, id);
CREATE INDEX ix_review_event_status ON review_event (status, review_type);

CREATE TABLE review_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_key TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_review', 'needs_evidence', 'resolved', 'rejected')),
    decision TEXT,
    reviewer TEXT,
    reviewed_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX ix_review_item_status ON review_item (status, category);
CREATE INDEX ix_review_item_object ON review_item (object_type, object_id);

CREATE TABLE asset_visual_signature (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    method_version TEXT NOT NULL,
    hash_hex TEXT NOT NULL,
    hash_bits INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    thumbnail_key TEXT,
    source_sha256 TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    UNIQUE (asset_id, method, method_version)
);

CREATE INDEX ix_visual_signature_hash ON asset_visual_signature (method, method_version, hash_hex);

CREATE TABLE visual_similarity_candidate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    left_asset_id INTEGER NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    right_asset_id INTEGER NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    method_version TEXT NOT NULL,
    distance INTEGER NOT NULL,
    threshold INTEGER NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'reviewed', 'rejected')),
    evidence_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (left_asset_id < right_asset_id),
    UNIQUE (left_asset_id, right_asset_id, method, method_version)
);

CREATE INDEX ix_visual_candidate_distance ON visual_similarity_candidate (distance, review_status);
CREATE INDEX ix_visual_candidate_left ON visual_similarity_candidate (left_asset_id);
CREATE INDEX ix_visual_candidate_right ON visual_similarity_candidate (right_asset_id);

CREATE TABLE visual_scan_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method TEXT NOT NULL,
    method_version TEXT NOT NULL,
    threshold INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    counts_json TEXT,
    errors_json TEXT
);
