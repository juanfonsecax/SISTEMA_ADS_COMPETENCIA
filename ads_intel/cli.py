from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import DEFAULT_BACKUP_DIR, DEFAULT_DB_PATH, DEFAULT_MANIFEST_PATH, REPO_ROOT
from .db import connect
from .importers import import_all
from .manifest import freeze
from .reconcile import build_report


def _freeze(args: argparse.Namespace) -> int:
    result = freeze(
        root=Path(args.root).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        backup_dir=Path(args.backup_dir).resolve(),
        include_images=not args.no_images,
        do_backup=not args.no_backup,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _import(args: argparse.Namespace) -> int:
    counts = import_all(Path(args.root).resolve(), Path(args.db).resolve())
    print(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _reconcile(args: argparse.Namespace) -> int:
    connection = connect(Path(args.db).resolve())
    try:
        report = build_report(connection)
    finally:
        connection.close()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def _all(args: argparse.Namespace) -> int:
    freeze(
        root=Path(args.root).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        backup_dir=Path(args.backup_dir).resolve(),
        include_images=not args.no_images,
        do_backup=not args.no_backup,
    )
    counts = import_all(Path(args.root).resolve(), Path(args.db).resolve())
    print(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True))
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
