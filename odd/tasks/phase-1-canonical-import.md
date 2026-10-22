# Phase 1 - Canonical model, provenance and legacy import

## Objective

Create a canonical SQLite model for the 597 retained ads, import every legacy artifact without modifying it, preserve provenance and one observation per ad/date, and prove import/reimport reconciliation with tests.

## Scope

- Freeze a SHA256 manifest of legacy data files and 597 images.
- Create `ads_intel` Python package, SQLite migrations, CLI and tests.
- Import `_ADS.csv`, `_BANCO.csv`, `_PAGINAS.csv`, `_RANKING_CUENTAS.csv`, `_COPIES.csv`, `_PRECLASIFICACION.csv`, `_CLASIF_FAVORITOS.csv`, `_ETIQUETAS_MANUALES.csv`, `_SELECCION_EXTRACCION.csv`, `_ELEMENTOS.csv`, `_BANCO_CREATIVOS/_INDICE.csv`, 111 fichas, 22 canonicos, 4 blueprints and 4 filled T01 documents.
- Resolve advertisers by `page_id`; preserve 10 known name aliases.
- Create source, batch, payload, creative, observation, asset, copy, tag, score snapshot, reference, product, fact, claim and issue records.
- Keep legacy files read-only; no `dedup.py`, no file deletion, no image moves.

## Tasks

- [x] A1. Create package, migration and CLI skeleton.
- [x] A2. Build legacy manifest and SHA256 image metadata.
- [x] A3. Implement canonical schema and migration runner.
- [x] A4. Import ads, pages, ranking snapshots, aliases, assets, observations and copies.
- [x] A5. Import tags, favorites, scores, element matrix and reference documents.
- [x] A6. Import Tinnidrop product facts and claims without approval.
- [x] A7. Add reconciliation report and import issues.
- [x] A8. Add unittest coverage for counts, idempotency, aliases, orphan copies, provenance and non-mutation.
- [x] A9. Run tests and produce the real baseline database.

## Acceptance

- 597 ads, 597 assets, 597 observations, 111 favorites, 111 fichas, 22 canonicos, 4 blueprints.
- 89 advertisers by `page_id`, 10 aliases, 95 total advertiser names and 60 ranking snapshots.
- Reimport is idempotent for domain tables.
- Legacy files are byte-identical before and after import.
- Three orphan `_COPIES.csv` rows are preserved as issues, not dropped.
- Claims are `evidence_needed`, never `approved`.
- `python -m unittest discover -s tests -v` passes.

## Verification evidence

- Manifest: `data/manifests/legacy_manifest.json`; 238 tracked legacy files, 597 images, 40,664,665 image bytes, 597 images with dimensions.
- Backup: `data/backups/legacy_snapshot_20261022T220926Z.zip`.
- Database: `data/ads_intel.db`; local/generated and gitignored.
- Import counts: 89 advertisers, 10 aliases, 95 names, 60 ranking snapshots, 597 creatives, 597 observations, 597 assets, 629 copy rows, 1,041 tags, 190 reference documents, 7 evidence-needed claims, 1,742 source payloads and 10 import issues.
- Tests: `python -m unittest discover -s tests -v` -> 16 tests, OK in 5.804s.
- Reconciliation: `python -m ads_intel.cli reconcile` -> `ok: true`, all checks pass.
- Legacy non-mutation: tests hash every declared legacy file before and after import; byte-identical.

## Next step

Dual-run review of gallery counts against the database, then Phase 2 asset similarity work.

