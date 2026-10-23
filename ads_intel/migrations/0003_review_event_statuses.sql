CREATE TABLE review_event_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    review_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'pending',
        'in_review',
        'needs_evidence',
        'resolved',
        'rejected',
        'approved',
        'restricted',
        'unknown',
        'evidence_needed'
    )),
    evidence_ref TEXT,
    reviewer TEXT,
    reviewed_at TEXT,
    notes TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

INSERT INTO review_event_new
    (id, object_type, object_id, review_type, status, evidence_ref, reviewer,
     reviewed_at, notes, payload_json, created_at)
SELECT id, object_type, object_id, review_type, status, evidence_ref, reviewer,
       reviewed_at, notes, payload_json, created_at
FROM review_event;

DROP TABLE review_event;

ALTER TABLE review_event_new RENAME TO review_event;

CREATE INDEX ix_review_event_object ON review_event (object_type, object_id, id);
CREATE INDEX ix_review_event_status ON review_event (status, review_type);
