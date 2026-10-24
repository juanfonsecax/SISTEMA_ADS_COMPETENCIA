# Phase 2.2 — Technical closeout and legacy retirement

## Objective

Fix the Phase 2.1 defects, make the new application self-contained, retire the legacy
programs that have no consumers, and prove that a clean checkout can start, migrate,
import, review, scan, and restore without them.

## Constraints

- Branch `fix/phase1-integrity`; no commit, no push, no change to `main`.
- Preserve all existing local changes.
- Never run capture against external sources.
- Never auto-approve permissions, rights, or claims.
- Never present perceptual similarity as identity proof.
- Never delete data required by the canonical application.
- No graphical interface or real export feature is claimed.

## Tasks

| ID | Task | Route | Status |
|----|------|-------|--------|
| T1 | Migration 0003: expand `review_event.status`, preserve rows, validate every allowed/rejected status | inline | done |
| T2 | Migration 0004 + `visuals.py`: bind candidates to `visual_scan_run`, latest-run view, historical query | inline | done |
| T3 | Inventory policy: active code, operational data, full recovery manifest; pre-cleanup F2 backup + restore proof | inline | done |
| T4 | Retire legacy capture/dedup/gallery/encoder scripts and obsolete operational docs/HTML | inline | done |
| T5 | Single entry point, README rewrite, install/migrate/backup/restore documentation | inline | done |
| T6 | Full validation: from-zero and upgrade migrations, governance states, scan thresholds, idempotency, integrity, restore, no legacy references | inline | done |

## Checks

- `python -m unittest discover -v`
- `python -m ads_intel.cli reconcile`
- `PRAGMA integrity_check`, `PRAGMA foreign_key_check`
- From-zero migration and upgrade of the pre-Phase-2 snapshot
- Visual scan at threshold 8 then 0; latest view must not show stale candidates
- Recovery backup restore report `ok: true`
- Clean-environment smoke run without legacy scripts

## Evidence

- Pre-cleanup recovery backup: `data/backups/phase1_full_20261022T231325Z.zip`, restore verified before changes.
- F2 pre-cleanup backup: `data/backups/phase2_recovery_20261023T023509Z.zip`, `ok: true`, 1593 archived files.
- Live schema upgrade: `0003_review_event_statuses`, `0004_visual_candidate_runs`; integrity `ok`, foreign keys `[]`.
- Final recovery backup via `python -m ads_intel.cli backup`: `data/backups/phase2_recovery_20261023T024131Z.zip`, `ok: true`, 1581 recoverable files plus database and control manifests.
- CLI restore smoke test: extracted to a temporary directory, database and code present, no retired script present.
- Tests: `python -m unittest discover -s tests -v` -> 42 tests OK.
- Live reconciliation: `python -m ads_intel.cli reconcile` -> `ok: true`, 34 checks pass.
- Live review queue: 22 pending items; no approvals recorded.
- Live visual state: 2 scan runs, 8 pending candidates; latest run id 2, threshold 8, 597 signatures.
- Legacy removal: 20 files deleted, `analisis-ad-2026-08-18.md` preserved under `ANALISIS/`; no code imports the retired programs.

## TDD

No project TDD setting is configured. Functional checks and regression tests are required
for every changed behavior.

## Recovery mirror

Engram is unavailable in this session; the task document is the source of truth.
