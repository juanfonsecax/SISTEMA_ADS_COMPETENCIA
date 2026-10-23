# Phase 2 - Asset intelligence and human review

## Objective

Add traceable provenance and rights review, a non-destructive human-review queue, perceptual image similarity candidates, and reconciliation coverage without changing the canonical legacy base.

## Scope

- A: Source permission records and per-asset rights records with evidence, reviewer, date, notes, and explicit statuses.
- B: Human-review items for legacy taxonomy, the FDA/MSPAS document conflict, Tinnidrop claims, the dead page with reported active ads, unnamed pages, and orphan copies.
- C: Versioned perceptual signatures, thumbnails under `data/`, and pending visual-similarity candidates for the 597 canonical JPG assets.
- D: Reconciliation, idempotency, reversibility, and no-loss tests for the new tables and scans.

## Constraints

- Do not delete, move, merge, or rewrite source images or legacy directories.
- Do not run `dedup.py`, `bajar.py`, `bajar2.py`, `_EXTRACTOR.js`, or `integrar_copies.py`.
- Do not regenerate `_ELEMENTOS.csv` or overwrite manual classifications.
- Do not approve claims, grant rights, or resolve human-review items automatically.
- Do not claim two images are duplicate copies based only on a perceptual hash; emit pending candidates with method, version, distance, and threshold.
- Unknown rights remain unknown. Approved export requires authorization evidence.
- Do not commit, push, or modify `main`; this follows the explicit F0/F1 user instruction.
- The image dependency must be declared and documented before use.

## Tasks

- [x] P2-0 Verify branch, HEAD, canonical counts, tests, and restorable backup; read the Phase 2 blueprint.
- [x] P2-1 Add migration for review events, review queue, versioned visual signatures, and similarity candidates.
- [x] P2-2 Implement provenance/rights/claim review services and approval guards.
- [x] P2-3 Seed the human-review queue without making decisions; expose a review listing.
- [x] P2-4 Implement image signature, thumbnail, and candidate service using the declared Pillow dependency.
- [x] P2-5 Add CLI commands for review queue/listing, governance updates, and visual scans.
- [x] P2-6 Extend reconciliation and tests for no-loss, idempotency, approval guards, failed images, hashes, thumbnails, and candidate quality.
- [x] P2-7 Run full tests, integrity checks, live import, visual scan, and report counts/evidence.

## Acceptance

- Existing 19 tests continue to pass; all 32 tests pass.
- `PRAGMA integrity_check` is `ok`; `PRAGMA foreign_key_check` is empty.
- 597 creatives, observations, assets, and ad-assets remain; all 597 asset paths exist; original image SHA-256 values are unchanged.
- 597 visual signatures are created; thumbnails are written only under `data/`; candidate rows are pending and explainable.
- Exact duplicates, minor variants, crops, and false-positive fixtures behave as documented candidates.
- All source/asset/claim approvals require evidence and reviewer; unknown rights are never exported as approved.
- Review items retain pending human decisions across repeated imports.
- No commit, no push, `main` untouched.

## Evidence

- Phase 2 Step 0: branch `fix/phase1-integrity`, HEAD `a6666005cadda33b9503abb459a8f20d9678582d`, 19 tests OK, reconciliation green, snapshot restore verified.
- Pre-Phase-2 backup: `data/backups/phase1_full_20261022T231325Z.zip`, SHA-256 `a50aea9d7145565cfd8bab1c8e4ecf8462eb23a22bc8d83e4916ec5fad00bec6`.
- Blueprint read from `C:\Users\juand\Downloads\Blueprint_Maestro_Inteligencia_Creativa_Ads_v1.md`; it is outside the repository.

## Route

Authorized Phase 2 implementation, direct inline with focused tests. Explicit user instruction overrides the usual work-unit commit rule; no commit or push.

## Final Evidence

- Implementation: `ads_intel/migrations/0002_asset_intelligence.sql`, `ads_intel/governance.py`, `ads_intel/review.py`, `ads_intel/visuals.py`; CLI/reconciliation/tests updated.
- Dependency: Pillow 12.3.0, declared in `requirements.txt` and documented in `README.md`; no other new dependency.
- Final tests: 32 tests OK in 13.708s (2026-10-22).
- Live import: 597 creatives, observations, assets, and ad-assets; 22 pending review items; 0 review decisions; 7 claims with 0 approved; 597/597 rights still `unknown`; source still `pending_review`.
- Reference documents: 191 = 190 canonical-base documents plus one historical `CATALOGO_CONCEPTOS` version. The reconciliation check accounts for versioned catalog rows without dropping history.
- Visual scan: two completed runs; 597 signatures; 597 thumbnails under `data/visual_thumbnails/`; 8 pending candidates; 0 failed; 0 exact SHA matches; method `dhash` version `1`, threshold 8.
- Image integrity: 597 paths exist; 0 SHA-256 mismatches; 597 assets have perceptual hashes; original images unchanged.
- SQLite: `PRAGMA integrity_check` = `ok`; `PRAGMA foreign_key_check` = empty.
- Export guard: `export-check --object source --object-id 1` returned `exportable: false` and exit 1.
- Modified tracked files: `README.md`, `ads_intel/{cli,config,importers,reconcile}.py`, `tests/{test_canonical_import,test_manifest}.py`; new untracked files include the migration, governance/review/visual modules, requirements, task document, and focused tests. No commit, no push, `main` untouched.
