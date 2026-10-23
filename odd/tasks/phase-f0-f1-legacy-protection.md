# Phase F0+F1 — Protect legacy and close canonical-base defects

## Objective

Protect the current repository state with a restorable SHA-256 snapshot, then correct the verified Phase 1 defects without moving legacy directories, changing manual classifications, approving claims, or starting Phase 2.

## Scope

- Complete tracked + local-data inventory and restorable backup.
- Catalog parser repair and non-null canonical definitions.
- Stronger byte-identity and reconciliation tests.
- Manifest/backup correctness for tracked files, images, reference assets, and local data.
- No physical reorganization.
- No commit or push; branch `fix/phase1-integrity`; `main` untouched.

## Constraints

- Do not delete or move `_IMG`, `_RAW`, `_BLUEPRINTS`, `ANALISIS`, or `_BANCO_CREATIVOS`.
- Do not run `dedup.py`, `bajar.py`, `bajar2.py`, `_EXTRACTOR.js`, or `integrar_copies.py`.
- Do not regenerate `_ELEMENTOS.csv`.
- Do not modify manual classifications or approve Tinnidrop claims.
- Do not introduce new providers or dependencies.
- Do not start Phase 2 features.

## Tasks

- [x] F0-1 Verify branch, HEAD, clean Git state, DB, migrations, tests.
- [x] F0-2 Create full SHA-256 manifest for all tracked files, images, reference assets, and stable local data.
- [x] F0-3 Create separate ignored local-data inventory.
- [x] F0-4 Create restorable full backup without overwriting prior backups.
- [x] F0-5 Restore backup to a temporary directory and verify hashes, counts, and DB counts.
- [x] F1-1 Repair catalog parser and recover C1–C9 definitions from `_CATALOGO_CONCEPTOS.md`.
- [x] F1-2 Add regression test that fails if canonical definitions are NULL.
- [x] F1-3 Expand no-mutation coverage to all tracked files, images, `_RAW`, reference assets, analysis modules, and documents.
- [x] F1-4 Correct manifest/backup logic to account for every tracked file once.
- [x] F1-5 Verify 597 ads, 597 images, 111 favorites, 48 references, 111 fichas, 22 canónicos, 4 blueprints, 85 pages with data, 10 aliases, 3 orphan copies.
- [x] F1-6 Run tests, SQLite integrity/FK checks, reconciliation, image-path check, and idempotent reimport.
- [x] F1-7 Produce before/after evidence, modified-file list, and residual human decisions.

## Acceptance

- Full manifest has no duplicate paths; every entry has SHA-256; counts are explicit.
- Backup restore has zero missing, zero mismatched, zero extra files; DB counts match.
- Canonical concept definitions are non-NULL for the eight active concepts; C6 remains retired and is not invented.
- Tests fail on unexpected mutation of any tracked file.
- All tests pass; `PRAGMA integrity_check` returns `ok`; foreign keys are clean.
- Reconciliation remains green; 597 asset paths exist; reimport is idempotent for domain tables.
- No commit, no push, no change to `main`.

## Evidence

- Baseline tests: 16 tests OK in 4.931s (2026-10-22, branch `fix/phase1-integrity`).
- F0 full backup: `data/backups/phase1_full_20261022T225938Z.zip` (114.491.319 bytes, SHA-256 `4a06356553b35bc4adddae865189f5b98e5f6d7f8671ab98c430100ed57a606a`).
- F0 manifest: `data/manifests/full_manifest_20261022T225938Z.json`; restore report `data/manifests/phase1_f0_restore_report_20261022T225938Z.json` -> `ok: true`, 0 missing, 0 mismatch, 0 extra.
- Post-F1 full snapshot: `data/backups/phase1_full_20261022T231325Z.zip` (60.488.001 bytes, SHA-256 `a50aea9d7145565cfd8bab1c8e4ecf8462eb23a22bc8d83e4916ec5fad00bec6`); report `data/manifests/phase1_restore_report_20261022T231325Z.json` -> `ok: true`, 980 entries, 983 restored files, 0 missing/mismatch/extra. Prior snapshots are inventoried with hashes and excluded from this zip to avoid recursive bloat; they remain on disk.
- Final tests: 19 tests OK in 9.545s. New coverage: 949 tracked files byte-identical, 597 unique images, 48 references hash-match `_IMG`, 8 non-NULL concept definitions, C6 absent from `concepto`, 85 pages with creatives, 4 dead pages.
- SQLite: `PRAGMA integrity_check` = `ok`; `PRAGMA foreign_key_check` = empty; 597/597 asset paths exist.
- Reconcile: `ok: true`; 597 creatives/observations/assets/ad_assets, 629 copies, 89 advertisers, 10 aliases, 111 favorites, 48 references, 111 fichas, 22 canónicos, 4 blueprints, 3 orphan copies, 7 claims with 0 approved.
- Catalog definitions repaired in the live DB: C1, C2, C3, C4, C5, C7, C8, C9 have non-NULL definitions; `SIN_CLASIFICAR` remains NULL; `C6_UNBOXING` survives only as a raw legacy tag in two favorites, not as a canonical concept.
- Modified tracked files: `_BANCO_CREATIVOS/_LEEME.md`, `_CATALOGO_CONCEPTOS.md`, `_HANDOFF.md`, `ads_intel/config.py`, `ads_intel/importers.py`, `ads_intel/manifest.py`, `ads_intel/util.py`, `tests/test_canonical_import.py`, `tests/test_manifest.py`.
- New untracked files: `odd/tasks/phase-f0-f1-legacy-protection.md`, `scripts/full_snapshot.py`. No commit, no push, `main` untouched.

## Route

Authorized F0 protection then F1 corrections, direct implementation with tests. No commit/push per explicit user instruction; this overrides the normal work-unit commit rule.
