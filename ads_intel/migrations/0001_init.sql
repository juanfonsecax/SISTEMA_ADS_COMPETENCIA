CREATE TABLE source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    terms_url TEXT,
    permission_basis TEXT NOT NULL DEFAULT 'pending_review',
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE capture_batch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    legacy_file TEXT,
    observed_on TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    imported_at TEXT NOT NULL,
    query_config_json TEXT NOT NULL,
    status TEXT NOT NULL,
    counts_json TEXT,
    errors_json TEXT,
    operator_id TEXT,
    notes TEXT,
    UNIQUE (source_id, observed_on, legacy_file)
);

CREATE TABLE source_payload (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    batch_id INTEGER REFERENCES capture_batch(id) ON DELETE SET NULL,
    external_id TEXT,
    raw_json TEXT NOT NULL,
    raw_hash TEXT NOT NULL,
    legacy_file TEXT NOT NULL,
    legacy_row INTEGER,
    fetched_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (legacy_file, legacy_row, raw_hash)
);

CREATE TABLE advertiser (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    external_page_id TEXT NOT NULL,
    name TEXT,
    page_url TEXT,
    country TEXT,
    niche TEXT,
    reported_active_ads INTEGER,
    reported_oldest_ad_days INTEGER,
    legacy_status TEXT,
    source_folder TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (source_id, external_page_id)
);

CREATE TABLE advertiser_alias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id INTEGER NOT NULL REFERENCES advertiser(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    first_seen_at TEXT,
    last_seen_at TEXT,
    source_file TEXT,
    UNIQUE (advertiser_id, name)
);

CREATE TABLE ad_creative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    external_ad_id TEXT NOT NULL,
    advertiser_id INTEGER NOT NULL REFERENCES advertiser(id) ON DELETE RESTRICT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    canonical_hash TEXT,
    review_state TEXT NOT NULL DEFAULT 'imported',
    is_catalog INTEGER NOT NULL DEFAULT 0 CHECK (is_catalog IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (source_id, external_ad_id)
);

CREATE TABLE ad_observation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_creative_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES capture_batch(id) ON DELETE RESTRICT,
    observed_on TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    reported_status TEXT,
    active_days_reported INTEGER,
    observed_rank INTEGER,
    observed_total INTEGER,
    page_active_ads_reported INTEGER,
    page_oldest_ad_days_reported INTEGER,
    reported_collation_count INTEGER,
    computed_same_image_count INTEGER,
    quadrant_legacy TEXT,
    source_payload_id INTEGER NOT NULL REFERENCES source_payload(id) ON DELETE RESTRICT,
    reported_velocity REAL,
    created_at TEXT NOT NULL,
    UNIQUE (ad_creative_id, observed_on, batch_id)
);

CREATE TABLE asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    source_url TEXT,
    mime_type TEXT,
    sha256 TEXT NOT NULL UNIQUE,
    md5 TEXT,
    perceptual_hash TEXT,
    width INTEGER,
    height INTEGER,
    bytes INTEGER,
    rights_status TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE ad_asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_creative_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES asset(id) ON DELETE RESTRICT,
    role TEXT NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 1,
    source_confidence REAL,
    UNIQUE (ad_creative_id, asset_id, role)
);

CREATE TABLE ad_copy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_creative_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    primary_text TEXT,
    headline TEXT,
    description TEXT,
    cta TEXT,
    destination_url TEXT,
    language TEXT,
    extraction_method TEXT NOT NULL,
    confidence REAL,
    confidence_label TEXT,
    is_canonical INTEGER NOT NULL DEFAULT 0 CHECK (is_canonical IN (0, 1)),
    source_file TEXT,
    source_row INTEGER,
    source_payload_id INTEGER REFERENCES source_payload(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX ux_ad_copy_canonical
    ON ad_copy (ad_creative_id)
    WHERE is_canonical = 1;

CREATE UNIQUE INDEX ux_ad_copy_legacy
    ON ad_copy (ad_creative_id, extraction_method, source_file, source_row)
    WHERE is_canonical = 0;

CREATE TABLE ad_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_ad_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    to_ad_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    method TEXT NOT NULL,
    confidence REAL,
    review_status TEXT NOT NULL DEFAULT 'pending',
    evidence_json TEXT,
    created_at TEXT NOT NULL,
    CHECK (from_ad_id <> to_ad_id)
);

CREATE TABLE tag_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension TEXT NOT NULL,
    tag_key TEXT NOT NULL,
    label TEXT NOT NULL,
    definition TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    source TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (dimension, tag_key, version)
);

CREATE TABLE ad_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_creative_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    asset_id INTEGER REFERENCES asset(id) ON DELETE CASCADE,
    tag_definition_id INTEGER NOT NULL REFERENCES tag_definition(id) ON DELETE RESTRICT,
    confidence REAL,
    confidence_label TEXT,
    assigned_by TEXT NOT NULL,
    method TEXT NOT NULL,
    model_version TEXT,
    prompt_version TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    evidence_json TEXT,
    source_file TEXT,
    source_row INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE (ad_creative_id, tag_definition_id, method, assigned_by)
);

CREATE TABLE legacy_score_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_creative_id INTEGER NOT NULL REFERENCES ad_creative(id) ON DELETE CASCADE,
    score_type TEXT NOT NULL,
    score_value REAL NOT NULL,
    source_file TEXT NOT NULL,
    source_row INTEGER,
    details_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (ad_creative_id, score_type, source_file, source_row)
);

CREATE TABLE legacy_element_observation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    selection_n INTEGER,
    ad_creative_id INTEGER REFERENCES ad_creative(id) ON DELETE SET NULL,
    advertiser TEXT,
    product TEXT,
    payload_json TEXT NOT NULL,
    source_file TEXT NOT NULL,
    source_row INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE (source_file, source_row)
);

CREATE TABLE reference_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    external_key TEXT NOT NULL,
    ad_creative_id INTEGER REFERENCES ad_creative(id) ON DELETE SET NULL,
    version TEXT,
    payload_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'imported',
    source_file TEXT NOT NULL,
    source_row INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE (kind, external_key, content_hash)
);

CREATE TABLE product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    market TEXT,
    category TEXT,
    sku TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    source_file TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX ux_product_name_brand
    ON product (name, COALESCE(brand, ''));

CREATE TABLE product_fact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    fact_key TEXT NOT NULL,
    value TEXT,
    unit TEXT,
    currency TEXT,
    evidence_ref TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    valid_from TEXT,
    valid_to TEXT,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX ux_product_fact_key
    ON product_fact (product_id, fact_key, COALESCE(valid_from, ''));

CREATE TABLE claim (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    claim_type TEXT,
    evidence_refs TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',
    markets TEXT,
    approved_by TEXT,
    reviewed_at TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (product_id, claim_text, claim_type)
);

CREATE TABLE import_issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_key TEXT NOT NULL UNIQUE,
    severity TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    source_file TEXT,
    source_row INTEGER,
    external_id TEXT,
    message TEXT NOT NULL,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE job_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    counts_json TEXT,
    errors_json TEXT
);

CREATE TABLE audit_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    event_type TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT,
    timestamp TEXT NOT NULL,
    before_hash TEXT,
    after_hash TEXT,
    reason TEXT
);

CREATE INDEX ix_capture_batch_source ON capture_batch (source_id, observed_on);
CREATE INDEX ix_source_payload_external ON source_payload (external_id);
CREATE INDEX ix_source_payload_hash ON source_payload (raw_hash);
CREATE INDEX ix_advertiser_page ON advertiser (external_page_id);
CREATE INDEX ix_ad_creative_advertiser ON ad_creative (advertiser_id);
CREATE INDEX ix_ad_creative_external ON ad_creative (external_ad_id);
CREATE INDEX ix_ad_observation_creative_date ON ad_observation (ad_creative_id, observed_on);
CREATE INDEX ix_ad_observation_batch ON ad_observation (batch_id);
CREATE INDEX ix_asset_md5 ON asset (md5);
CREATE INDEX ix_ad_asset_asset ON ad_asset (asset_id);
CREATE INDEX ix_ad_tag_creative ON ad_tag (ad_creative_id);
CREATE INDEX ix_ad_tag_definition ON ad_tag (tag_definition_id);
CREATE INDEX ix_ad_relation_from ON ad_relation (from_ad_id);
CREATE INDEX ix_ad_relation_to ON ad_relation (to_ad_id);
CREATE INDEX ix_reference_kind ON reference_document (kind, external_key);
CREATE INDEX ix_reference_ad ON reference_document (ad_creative_id);
CREATE INDEX ix_claim_product ON claim (product_id, status);
CREATE INDEX ix_import_issue_type ON import_issue (issue_type, severity);
