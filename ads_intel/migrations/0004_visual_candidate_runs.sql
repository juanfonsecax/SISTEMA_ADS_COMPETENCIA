CREATE TABLE visual_similarity_candidate_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_run_id INTEGER NOT NULL REFERENCES visual_scan_run(id) ON DELETE CASCADE,
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
    UNIQUE (scan_run_id, left_asset_id, right_asset_id, method, method_version)
);

INSERT INTO visual_similarity_candidate_new
    (id, scan_run_id, left_asset_id, right_asset_id, method, method_version,
     distance, threshold, review_status, evidence_json, created_at, updated_at)
SELECT c.id,
       (
           SELECT r.id
           FROM visual_scan_run r
           WHERE r.method = c.method AND r.method_version = c.method_version
           ORDER BY r.id DESC
           LIMIT 1
       ),
       c.left_asset_id,
       c.right_asset_id,
       c.method,
       c.method_version,
       c.distance,
       c.threshold,
       c.review_status,
       c.evidence_json,
       c.created_at,
       c.updated_at
FROM visual_similarity_candidate c;

DROP TABLE visual_similarity_candidate;

ALTER TABLE visual_similarity_candidate_new RENAME TO visual_similarity_candidate;

CREATE INDEX ix_visual_candidate_run ON visual_similarity_candidate (scan_run_id, distance, review_status);
CREATE INDEX ix_visual_candidate_distance ON visual_similarity_candidate (distance, review_status);
CREATE INDEX ix_visual_candidate_left ON visual_similarity_candidate (left_asset_id);
CREATE INDEX ix_visual_candidate_right ON visual_similarity_candidate (right_asset_id);
