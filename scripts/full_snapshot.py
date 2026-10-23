from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ads_intel.inventory import create_recovery_backup  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create and verify a full recovery backup (code, data, database snapshot)."
    )
    parser.add_argument("root", nargs="?", default=str(ROOT))
    parser.add_argument("--db")
    parser.add_argument("--manifest-dir")
    parser.add_argument("--backup-dir")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    destination = Path(args.backup_dir).resolve() if args.backup_dir else root / "data" / "backups"
    manifest_dir = Path(args.manifest_dir).resolve() if args.manifest_dir else root / "data" / "manifests"
    report = create_recovery_backup(
        root,
        destination,
        manifest_dir=manifest_dir,
        db_path=Path(args.db).resolve() if args.db else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
