# Phase 3 - Canonical taxonomy, classification, review, and explorer

## Objective

Extend the canonical `ads_intel` base with a versioned, multidimensional creative taxonomy, a traceable classification and human-review workflow, and an internal query/export service. Preserve every legacy label, asset, claim, and pending decision.

## Problem

The legacy base stores useful concepts and tags, but it mixes dimensions, lacks a versioned taxonomy, and has no first-class workflow for reviewing automatic suggestions. Phase 3 must separate concept, angle, format, style, audience, awareness, problem, desire, emotion, mechanism, proof, objection, offer, CTA, funnel context, compliance risk, language, and market without losing the original data.

## Scope

- Add versioned taxonomy and dimension definitions from the Blueprint (section 8.1) and the approved concept catalog.
- Add classification provenance, status, confidence basis, primary-tag support, and immutable status history.
- Map unambiguous legacy labels into canonical dimensions; leave ambiguous labels pending human review.
- Protect human-approved assignments from automatic overwrite.
- Extend review workflows to approve, correct, reject, and defer classification suggestions.
- Add explorer queries and CSV/JSONL export with provenance and a temporal cutoff.
- Define a future enrichment contract for OCR, vision, and language models, including output validation and cost tracking. Do not call a paid provider.
- Correct the Phase 2.2 closeout document from 40 to 34 checks.

## Constraints

- Work only on `feature/phase3-creative-intelligence`; do not commit, push, or merge.
- Do not rebuild `ads_intel` or restore retired legacy scripts.
- Use the Blueprint and `_CATALOGO_CONCEPTOS.md` as the source of definitions.
- C1-C5 and C7-C9 are canonical. C6 must not be recreated as canonical.
- Preserve 597 assets, 7 claims in `evidence_needed`, 22 review items pending, all unknown rights, and the 10 known import issues.
- Do not delete or merge ads, alter original images, approve rights, or resolve governance reviews automatically.
- Migrations must be non-destructive and work from an empty database and from the current schema.
- Do not invent numeric confidence for legacy tags.
- Automatic classification must not modify an approved human assignment.

## Tasks

- [x] P3-01 Create migration `0005_taxonomy_classification.sql` with taxonomy version, dimensions, mappings, classification runs, ad-tag history, and safe `ad_tag` extensions.
- [x] P3-02 Implement `ads_intel/taxonomy.py` with the canonical dimensions, tags, exact definitions, seeding, and validation.
- [x] P3-03 Implement `ads_intel/classification.py` with legacy mapping, run tracking, approved-tag protection, review lists, and human decisions.
- [x] P3-04 Implement `ads_intel/explorer.py` with multidimensional search, creative detail, unclassified/low-evidence detection, and provenance export.
- [x] P3-05 Implement `ads_intel/enrichment.py` with a validated future-model contract and cost/run tracking.
- [x] P3-06 Extend `ads_intel/cli.py` and `README.md` with taxonomy, classification-review, explorer, and export commands.
- [x] P3-07 Update reconciliation to preserve legacy counts while reporting Phase 3 taxonomy counts.
- [x] P3-08 Add tests for taxonomy versioning, legacy mapping, review transitions, approved-tag protection, explorer filters, export provenance, and enrichment validation.
- [x] P3-09 Correct `odd/tasks/phase-2.2-technical-closeout.md` from 40 to 34 reconciliation checks.
- [x] P3-10 Run the full test suite, reconciliation on a temporary database, migration-from-zero, and a migration on a copy of the live database.

## Acceptance criteria

- Canonical dimensions and concepts are versioned and queryable by dimension.
- Every classification keeps its source, method, version, status, confidence basis, and history.
- Legacy labels are preserved; unambiguous mappings create pending canonical assignments; ambiguous labels remain pending mappings.
- Approved human assignments cannot be changed by automatic runs.
- The review workflow supports approve, correct, reject, and defer without deleting history.
- Explorer queries filter by dimensions/tags, advertiser, market, language, and date, and expose unclassified/low-evidence creatives.
- Export includes provenance and respects a temporal cutoff.
- Enrichment output validation rejects unknown dimensions/tags and records cost; no provider is called.
- Existing canonical counts, 597 assets, 7 claims, 22 pending review items, unknown rights, and original files remain intact.
- Full test suite and migration checks pass.

## Verification

```text
python -m unittest discover -s tests -v
python -m ads_intel.cli --db <temp-db> reconcile
```

## Progress

- Created `feature/phase3-creative-intelligence` from `fix/phase1-integrity` at `108f522`.
- Added migration `0005_taxonomy_classification.sql`; from-zero and live-copy upgrades both apply cleanly.
- Taxonomy `1.0.0`: 21 dimensions, 97 canonical tags, 19 unambiguous legacy mappings, 10 ambiguous mappings pending review. C6 remains historical only and maps explicitly to C5. Total definitions are 136: 97 canonical tags plus 39 legacy-only labels.
- `classify-legacy` on a temporary database: 29 source labels, 19 mapped, 10 pending, 88 canonical assignments inserted, 124 protected existing assignments skipped, no errors.
- Approved-tag protection, correction/supersession, reject/defer, mapping decisions, explorer filters, export provenance/cutoff, and enrichment cost/protection are covered by tests.
- Reconciliation after classification is green: 1041 legacy `ad_tag` rows preserved, 199 canonical assignments, 88 pending, 10 mappings needing review.
- Full suite: `python -m unittest discover -s tests -v` -> 55 tests OK.
- Migration on a copy of the live database: `ok: true`, 37 checks pass, 597 assets, 7 claims, 22 pending review items, 597 unknown-rights assets, 1041 legacy tags, 97 canonical taxonomy tags.
- Live `data/ads_intel.db` was not modified. Changes remain uncommitted; no commit, push, or merge performed.
- P3-10 complete: migration-from-zero exercised by the test suite; temporary-database reconciliation and live-copy migration both pass.
