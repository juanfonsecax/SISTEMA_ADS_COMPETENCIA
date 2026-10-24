from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import (
    DEFAULT_BACKUP_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_MANIFEST_PATH,
    REPO_ROOT,
)
from .classification import (
    classification_context,
    classify_legacy,
    list_classifications,
    list_mappings,
    record_classification_review,
    record_mapping_decision,
)
from .db import apply_migrations, connect
from .enrichment import (
    enrichment_contract_schema,
    ingest_enrichment,
    list_enrichment_runs,
)
from .explorer import creative_detail, export_classifications, search_creatives
from .governance import (
    ApprovalError,
    assert_exportable,
    record_asset_rights_review,
    record_claim_review,
    record_source_review,
)
from .importers import import_all
from .inventory import create_recovery_backup, restore_recovery_backup
from .manifest import freeze
from .reconcile import build_report
from .review import list_review_items, record_review_decision, seed_review_queue
from .taxonomy import list_taxonomy, seed_taxonomy
from .visuals import (
    DEFAULT_THRESHOLD,
    list_visual_candidates,
    list_visual_scan_runs,
    scan_visual_similarity,
)


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True))


def _connection(args: argparse.Namespace):
    connection = connect(Path(args.db).resolve())
    apply_migrations(connection)
    return connection


def _freeze(args: argparse.Namespace) -> int:
    result = freeze(
        root=Path(args.root).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        backup_dir=Path(args.backup_dir).resolve(),
        include_images=not args.no_images,
        do_backup=not args.no_backup,
    )
    _print(result)
    return 0


def _import(args: argparse.Namespace) -> int:
    counts = import_all(Path(args.root).resolve(), Path(args.db).resolve())
    _print(counts)
    return 0


def _reconcile(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        report = build_report(connection, root=Path(args.root).resolve())
    finally:
        connection.close()
    _print(report)
    return 0 if report["ok"] else 1


def _review_seed(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        with connection:
            inserted = seed_review_queue(connection, Path(args.root).resolve())
        items = list_review_items(connection)
    finally:
        connection.close()
    _print({"inserted": inserted, "total": len(items)})
    return 0


def _review_list(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        items = list_review_items(connection, status=args.status, category=args.category)
    finally:
        connection.close()
    _print(items)
    return 0


def _review_decide(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        if not args.decision or not args.reviewer:
            raise ValueError("--decision and --reviewer are required")
        record_review_decision(
            connection,
            args.item_id,
            status=args.status,
            decision=args.decision,
            reviewer=args.reviewer,
            notes=args.notes,
            reviewed_at=args.reviewed_at,
        )
        items = [item for item in list_review_items(connection) if item["id"] == args.item_id]
    finally:
        connection.close()
    _print(items[0] if items else {"item_id": args.item_id, "updated": True})
    return 0


def _review_record(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        if args.object == "source":
            event_id = record_source_review(
                connection,
                args.object_id,
                status=args.status,
                permission_basis=args.permission_basis,
                evidence_ref=args.evidence_ref[0] if args.evidence_ref else None,
                reviewer=args.reviewer,
                reviewed_at=args.reviewed_at,
                notes=args.notes,
            )
        elif args.object == "asset":
            event_id = record_asset_rights_review(
                connection,
                args.object_id,
                status=args.status,
                evidence_ref=args.evidence_ref[0] if args.evidence_ref else None,
                reviewer=args.reviewer,
                reviewed_at=args.reviewed_at,
                notes=args.notes,
            )
        elif args.object == "claim":
            event_id = record_claim_review(
                connection,
                args.object_id,
                status=args.status,
                evidence_refs=args.evidence_ref,
                reviewer=args.reviewer,
                reviewed_at=args.reviewed_at,
                notes=args.notes,
            )
        else:
            raise ValueError(f"Unsupported object: {args.object}")
    finally:
        connection.close()
    _print({"event_id": event_id, "object": args.object, "object_id": args.object_id})
    return 0


def _export_check(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        assert_exportable(connection, args.object, args.object_id)
    except ApprovalError as exc:
        _print({"exportable": False, "object": args.object, "object_id": args.object_id, "reason": str(exc)})
        return 1
    finally:
        connection.close()
    _print({"exportable": True, "object": args.object, "object_id": args.object_id})
    return 0


def _visual_scan(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        root = Path(args.root).resolve()
        result = scan_visual_similarity(
            connection,
            root,
            threshold=args.threshold,
            thumbnail_root=Path(args.thumbnails).resolve()
            if args.thumbnails
            else root / "data" / "visual_thumbnails",
        )
    finally:
        connection.close()
    _print(result)
    return 0 if not result["failed"] else 1


def _visual_list(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        candidates = list_visual_candidates(
            connection,
            run_id=args.run_id,
            threshold=args.threshold,
            limit=args.limit,
        )
    finally:
        connection.close()
    _print(candidates)
    return 0


def _visual_runs(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        runs = list_visual_scan_runs(connection, limit=args.limit)
    finally:
        connection.close()
    _print(runs)
    return 0


def _taxonomy_seed(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        with connection:
            result = seed_taxonomy(connection, Path(args.root).resolve())
    finally:
        connection.close()
    _print(result)
    return 0


def _taxonomy_list(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        dimensions = list_taxonomy(connection, dimension=args.dimension)
    finally:
        connection.close()
    _print(dimensions)
    return 0


def _classify_legacy(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        with connection:
            result = classify_legacy(connection, root=Path(args.root).resolve())
    finally:
        connection.close()
    _print(result)
    return 0 if not result["errors"] else 1


def _classification_list(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        rows = list_classifications(
            connection,
            status=args.status,
            dimension=args.dimension,
            limit=args.limit,
            include_legacy=args.include_legacy,
        )
    finally:
        connection.close()
    _print(rows)
    return 0


def _classification_show(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        result = classification_context(connection, args.tag_id)
    finally:
        connection.close()
    _print(result)
    return 0


def _classification_review(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        with connection:
            result = record_classification_review(
                connection,
                args.tag_id,
                action=args.action,
                reviewer=args.reviewer,
                reason=args.reason,
                target_dimension=args.target_dimension,
                target_tag_key=args.tag_key,
                approve_correction=args.approve,
                primary=args.primary,
                reviewed_at=args.reviewed_at,
            )
    finally:
        connection.close()
    _print(result)
    return 0


def _mapping_list(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        rows = list_mappings(connection, status=args.status, source_dimension=args.source_dimension)
    finally:
        connection.close()
    _print(rows)
    return 0


def _mapping_decide(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        with connection:
            mapping = record_mapping_decision(
                connection,
                source_dimension=args.source_dimension,
                source_tag_key=args.source_key,
                target_dimension=args.target_dimension,
                target_tag_key=args.target_key,
                reviewer=args.reviewer,
                reason=args.reason,
            )
            classified = None if args.no_apply else classify_legacy(
                connection, root=Path(args.root).resolve()
            )
    finally:
        connection.close()
    _print({"mapping": mapping, "classification": classified})
    return 0


def _explore(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        tag_filters = []
        for value in args.tag or []:
            if ":" not in value:
                raise ValueError(f"Tag filter must be dimension:key, got {value!r}")
            dimension, key = value.split(":", 1)
            tag_filters.append((dimension.strip(), key.strip()))
        rows = search_creatives(
            connection,
            text=args.text,
            advertiser=args.advertiser,
            tag_filters=tag_filters,
            market=args.market,
            language=args.language,
            date_from=args.date_from,
            date_to=args.date_to,
            unclassified=args.unclassified,
            low_evidence=args.low_evidence,
            dimension_missing=args.missing_dimension,
            limit=args.limit,
            offset=args.offset,
        )
    finally:
        connection.close()
    _print(rows)
    return 0


def _creative_show(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        result = creative_detail(connection, args.creative_id)
    finally:
        connection.close()
    _print(result)
    return 0


def _export_classifications(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        result = export_classifications(
            connection,
            Path(args.output).resolve(),
            format=args.format,
            dimension=args.dimension,
            status=args.status,
            cutoff=args.cutoff,
            scope=args.scope,
        )
    finally:
        connection.close()
    _print(result)
    return 0


def _enrichment_contract(args: argparse.Namespace) -> int:
    _print(enrichment_contract_schema())
    return 0


def _enrichment_ingest(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    connection = _connection(args)
    try:
        with connection:
            result = ingest_enrichment(connection, payload)
    finally:
        connection.close()
    _print(result)
    return 0


def _enrichment_runs(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        rows = list_enrichment_runs(connection, limit=args.limit)
    finally:
        connection.close()
    _print(rows)
    return 0


def _backup(args: argparse.Namespace) -> int:
    result = create_recovery_backup(
        Path(args.root).resolve(),
        Path(args.backup_dir).resolve(),
        manifest_dir=Path(args.manifest).resolve().parent,
        db_path=Path(args.db).resolve(),
    )
    _print(result)
    return 0 if result["ok"] else 1


def _restore(args: argparse.Namespace) -> int:
    result = restore_recovery_backup(
        Path(args.archive).resolve(),
        Path(args.target).resolve(),
    )
    _print(result)
    return 0


def _all(args: argparse.Namespace) -> int:
    freeze(
        root=Path(args.root).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        backup_dir=Path(args.backup_dir).resolve(),
        include_images=not args.no_images,
        do_backup=not args.no_backup,
    )
    counts = import_all(Path(args.root).resolve(), Path(args.db).resolve())
    _print(counts)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ads_intel", description="Canonical import for SISTEMA_ADS_COMPETENCIA")
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--backup-dir", default=str(DEFAULT_BACKUP_DIR))
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze", help="Create legacy manifest and backup")
    freeze_parser.add_argument("--no-images", action="store_true")
    freeze_parser.add_argument("--no-backup", action="store_true")
    freeze_parser.set_defaults(func=_freeze)

    import_parser = subparsers.add_parser("import", help="Import legacy data into SQLite")
    import_parser.set_defaults(func=_import)

    reconcile_parser = subparsers.add_parser("reconcile", help="Check canonical counts")
    reconcile_parser.set_defaults(func=_reconcile)

    review_seed = subparsers.add_parser("review-seed", help="Create pending human-review items")
    review_seed.set_defaults(func=_review_seed)

    review_list = subparsers.add_parser("review-list", help="List human-review items")
    review_list.add_argument("--status", choices=["pending", "in_review", "needs_evidence", "resolved", "rejected"])
    review_list.add_argument("--category")
    review_list.set_defaults(func=_review_list)

    review_decide = subparsers.add_parser("review-decide", help="Record a human review decision")
    review_decide.add_argument("--item-id", type=int, required=True)
    review_decide.add_argument(
        "--status",
        required=True,
        choices=["in_review", "needs_evidence", "resolved", "rejected"],
    )
    review_decide.add_argument("--decision", required=True)
    review_decide.add_argument("--reviewer", required=True)
    review_decide.add_argument("--notes")
    review_decide.add_argument("--reviewed-at")
    review_decide.set_defaults(func=_review_decide)

    review_record = subparsers.add_parser("review-record", help="Record a source, asset, or claim review")
    review_record.add_argument("--object", required=True, choices=["source", "asset", "claim"])
    review_record.add_argument("--object-id", type=int, required=True)
    review_record.add_argument(
        "--status",
        required=True,
        choices=["pending", "approved", "restricted", "rejected", "needs_evidence", "evidence_needed", "unknown"],
    )
    review_record.add_argument("--permission-basis")
    review_record.add_argument("--evidence-ref", action="append")
    review_record.add_argument("--reviewer")
    review_record.add_argument("--reviewed-at")
    review_record.add_argument("--notes")
    review_record.set_defaults(func=_review_record)

    export_check = subparsers.add_parser("export-check", help="Fail unless an object has approved evidence")
    export_check.add_argument("--object", required=True, choices=["source", "asset", "claim"])
    export_check.add_argument("--object-id", type=int, required=True)
    export_check.set_defaults(func=_export_check)

    visual_scan = subparsers.add_parser("visual-scan", help="Compute hashes, thumbnails, and candidate pairs")
    visual_scan.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    visual_scan.add_argument("--thumbnails")
    visual_scan.set_defaults(func=_visual_scan)

    visual_list = subparsers.add_parser("visual-list", help="List current or historical visual candidates")
    visual_list.add_argument("--run-id", type=int, help="Inspect a specific historical scan run")
    visual_list.add_argument("--threshold", type=int)
    visual_list.add_argument("--limit", type=int)
    visual_list.set_defaults(func=_visual_list)

    visual_runs = subparsers.add_parser("visual-runs", help="List visual scan runs")
    visual_runs.add_argument("--limit", type=int)
    visual_runs.set_defaults(func=_visual_runs)

    taxonomy_seed = subparsers.add_parser("taxonomy-seed", help="Seed the active canonical taxonomy")
    taxonomy_seed.set_defaults(func=_taxonomy_seed)

    taxonomy_list = subparsers.add_parser("taxonomy-list", help="List canonical dimensions and tags")
    taxonomy_list.add_argument("--dimension")
    taxonomy_list.set_defaults(func=_taxonomy_list)

    classify_legacy_parser = subparsers.add_parser(
        "classify-legacy", help="Map legacy labels into canonical dimensions"
    )
    classify_legacy_parser.set_defaults(func=_classify_legacy)

    classification_list = subparsers.add_parser(
        "classification-list", help="List classification assignments for human review"
    )
    classification_list.add_argument(
        "--status",
        choices=["suggested", "pending_review", "reviewed", "approved", "rejected", "superseded"],
    )
    classification_list.add_argument("--dimension")
    classification_list.add_argument("--limit", type=int)
    classification_list.add_argument("--include-legacy", action="store_true")
    classification_list.set_defaults(func=_classification_list)

    classification_show = subparsers.add_parser(
        "classification-show", help="Show one assignment with creative, assets, tags, and history"
    )
    classification_show.add_argument("--tag-id", type=int, required=True)
    classification_show.set_defaults(func=_classification_show)

    classification_review = subparsers.add_parser(
        "classification-review", help="Approve, correct, reject, or defer a classification"
    )
    classification_review.add_argument("--tag-id", type=int, required=True)
    classification_review.add_argument(
        "--action", required=True, choices=["approve", "correct", "reject", "defer"]
    )
    classification_review.add_argument("--reviewer", required=True)
    classification_review.add_argument("--reason")
    classification_review.add_argument("--target-dimension")
    classification_review.add_argument("--tag-key")
    classification_review.add_argument("--approve", action="store_true", help="Approve a correction")
    classification_review.add_argument(
        "--primary", action=argparse.BooleanOptionalAction, default=None
    )
    classification_review.add_argument("--reviewed-at")
    classification_review.set_defaults(func=_classification_review)

    mapping_list = subparsers.add_parser("mapping-list", help="List legacy-to-canonical mappings")
    mapping_list.add_argument("--status", choices=["mapped", "needs_review", "rejected"])
    mapping_list.add_argument("--source-dimension")
    mapping_list.set_defaults(func=_mapping_list)

    mapping_decide = subparsers.add_parser(
        "mapping-decide", help="Resolve an ambiguous legacy label and apply the mapping"
    )
    mapping_decide.add_argument("--source-dimension", required=True)
    mapping_decide.add_argument("--source-key", required=True)
    mapping_decide.add_argument("--target-dimension", required=True)
    mapping_decide.add_argument("--target-key", required=True)
    mapping_decide.add_argument("--reviewer", required=True)
    mapping_decide.add_argument("--reason", required=True)
    mapping_decide.add_argument("--no-apply", action="store_true")
    mapping_decide.set_defaults(func=_mapping_decide)

    explore = subparsers.add_parser("explore", help="Search creatives across canonical dimensions")
    explore.add_argument("--text")
    explore.add_argument("--advertiser")
    explore.add_argument("--tag", action="append", help="Filter as dimension:key; repeatable")
    explore.add_argument("--market")
    explore.add_argument("--language")
    explore.add_argument("--from", dest="date_from")
    explore.add_argument("--to", dest="date_to")
    explore.add_argument("--unclassified", action="store_true")
    explore.add_argument("--low-evidence", action="store_true")
    explore.add_argument("--missing-dimension")
    explore.add_argument("--limit", type=int, default=50)
    explore.add_argument("--offset", type=int, default=0)
    explore.set_defaults(func=_explore)

    creative_show = subparsers.add_parser("creative-show", help="Show one creative with tags and assets")
    creative_show.add_argument("--creative-id", type=int, required=True)
    creative_show.set_defaults(func=_creative_show)

    export_classifications_parser = subparsers.add_parser(
        "export-classifications", help="Export classifications with provenance and cutoff"
    )
    export_classifications_parser.add_argument("--output", required=True)
    export_classifications_parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    export_classifications_parser.add_argument("--dimension")
    export_classifications_parser.add_argument(
        "--status",
        choices=["suggested", "pending_review", "reviewed", "approved", "rejected", "superseded"],
    )
    export_classifications_parser.add_argument("--cutoff")
    export_classifications_parser.add_argument("--scope", choices=["canonical", "all"], default="canonical")
    export_classifications_parser.set_defaults(func=_export_classifications)

    enrichment_contract = subparsers.add_parser(
        "enrichment-contract", help="Print the future enrichment contract"
    )
    enrichment_contract.set_defaults(func=_enrichment_contract)

    enrichment_ingest = subparsers.add_parser(
        "enrichment-ingest", help="Validate and ingest a future enrichment payload"
    )
    enrichment_ingest.add_argument("--input", required=True)
    enrichment_ingest.set_defaults(func=_enrichment_ingest)

    enrichment_runs = subparsers.add_parser("enrichment-runs", help="List enrichment runs and costs")
    enrichment_runs.add_argument("--limit", type=int, default=20)
    enrichment_runs.set_defaults(func=_enrichment_runs)

    backup_parser = subparsers.add_parser(
        "backup", help="Create and verify a full code, data, and database recovery backup"
    )
    backup_parser.set_defaults(func=_backup)

    restore_parser = subparsers.add_parser("restore", help="Extract a recovery backup")
    restore_parser.add_argument("archive")
    restore_parser.add_argument("target")
    restore_parser.set_defaults(func=_restore)

    all_parser = subparsers.add_parser("all", help="Freeze and import")
    all_parser.add_argument("--no-images", action="store_true")
    all_parser.add_argument("--no-backup", action="store_true")
    all_parser.set_defaults(func=_all)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
