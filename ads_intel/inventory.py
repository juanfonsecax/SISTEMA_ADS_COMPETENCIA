from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import DEFAULT_DB_PATH
from .util import sha256_file, utc_now, write_json

CODE_PREFIXES = ("ads_intel/", "tests/", "scripts/", "odd/tasks/")
CODE_ROOT_FILES = {".gitignore", "README.md", "requirements.txt"}

DATA_PREFIXES = ("_IMG/", "_BANCO_CREATIVOS/", "_BLUEPRINTS/", "_RAW/", "ANALISIS/", "data/")
OPERATIONAL_ROOT_FILES = {
    "_ADS.csv",
    "_BANCO.csv",
    "_PAGINAS.csv",
    "_COPIES.csv",
    "_RANKING_CUENTAS.csv",
    "_PRECLASIFICACION.csv",
    "_CLASIF_FAVORITOS.csv",
    "_ETIQUETAS_MANUALES.csv",
    "_SELECCION_EXTRACCION.csv",
    "_ELEMENTOS.csv",
    "_CATALOGO_CONCEPTOS.md",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}
SECRET_NAMES = {".env"}
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
TRANSIENT_SUFFIXES = (".pyc", ".pyo", ".db-wal", ".db-shm")


def _posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_secret(path: Path) -> bool:
    if path.name in SECRET_NAMES or path.name.startswith(".env."):
        return True
    return path.suffix.lower() in SECRET_SUFFIXES


def _is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_DIR_NAMES for part in relative.parts[:-1]):
        return True
    if path.suffix.lower() in TRANSIENT_SUFFIXES:
        return True
    return _is_secret(path)


def _iter_files(root: Path, prefixes: Iterable[str] | None = None) -> Iterable[Path]:
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_excluded(path, root):
            continue
        relative = _posix(path, root)
        if prefixes is not None and not any(relative.startswith(prefix) for prefix in prefixes):
            continue
        yield path


def _category(relative: str) -> str:
    if relative.startswith("ads_intel/"):
        return "code"
    if relative.startswith("tests/"):
        return "test"
    if relative.startswith("scripts/"):
        return "script"
    if relative.startswith("odd/"):
        return "governance"
    if relative in CODE_ROOT_FILES:
        return "config"
    if relative.startswith("_IMG/"):
        return "image"
    if relative.startswith("_BANCO_CREATIVOS/"):
        return "reference_asset"
    if relative.startswith("_BLUEPRINTS/"):
        return "blueprint_or_ficha"
    if relative.startswith("_RAW/"):
        return "raw_capture"
    if relative.startswith("ANALISIS/"):
        return "research"
    if relative.startswith("data/"):
        return "operational_data"
    if relative.endswith(".csv"):
        return "source_data"
    if relative.endswith((".py", ".js")):
        return "legacy_code"
    if relative.endswith((".html", ".css")):
        return "generated_view"
    if relative.endswith((".md", ".txt")):
        return "documentation"
    return "other"


def _scope(relative: str) -> str:
    if relative.startswith(CODE_PREFIXES) or relative in CODE_ROOT_FILES:
        return "active_code"
    if relative.startswith(DATA_PREFIXES) or relative in OPERATIONAL_ROOT_FILES:
        return "operational_data"
    category = _category(relative)
    if category in {"legacy_code", "generated_view", "documentation"}:
        return "legacy_evidence"
    if category == "research":
        return "research"
    return "other"


def _entry(path: Path, root: Path) -> dict[str, Any]:
    relative = _posix(path, root)
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "category": _category(relative),
        "scope": _scope(relative),
    }


def _file_entries(paths: Iterable[Path], root: Path) -> list[dict[str, Any]]:
    return [_entry(path, root) for path in paths]


def build_code_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = _file_entries(
        (
            path
            for path in _iter_files(root)
            if _posix(path, root).startswith(CODE_PREFIXES)
            or _posix(path, root) in CODE_ROOT_FILES
        ),
        root,
    )
    return {
        "schema": "active-code-inventory-v1",
        "generated_at": utc_now(),
        "root_name": root.name,
        "files": files,
        "counts": {
            "files": len(files),
            "bytes": sum(item["bytes"] for item in files),
            "by_category": dict(Counter(item["category"] for item in files)),
        },
    }


def build_data_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    paths = [
        path
        for path in _iter_files(root)
        if _posix(path, root).startswith(DATA_PREFIXES)
        or _posix(path, root) in OPERATIONAL_ROOT_FILES
    ]
    files = []
    database = None
    for path in paths:
        relative = _posix(path, root)
        if relative == "data/ads_intel.db":
            database = {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            continue
        if relative.startswith("data/backups/"):
            continue
        files.append(_entry(path, root))
    return {
        "schema": "operational-data-inventory-v1",
        "generated_at": utc_now(),
        "root_name": root.name,
        "database_source": database,
        "files": files,
        "counts": {
            "files": len(files),
            "bytes": sum(item["bytes"] for item in files),
            "by_category": dict(Counter(item["category"] for item in files)),
            "previous_backups_excluded": len(list((root / "data" / "backups").glob("*.zip"))),
        },
    }


def _previous_backups(root: Path) -> list[Path]:
    directory = root / "data" / "backups"
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.zip") if path.is_file())


def build_recovery_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    previous = {path.resolve() for path in _previous_backups(root)}
    files = []
    excluded = []
    for path in _iter_files(root):
        if path.resolve() in previous:
            excluded.append({"path": _posix(path, root), "reason": "previous backup; not nested"})
            continue
        if path.resolve() == (root / "data" / "ads_intel.db").resolve():
            continue
        files.append(_entry(path, root))
    return {
        "schema": "recovery-manifest-v1",
        "generated_at": utc_now(),
        "root_name": root.name,
        "files": files,
        "counts": {
            "files": len(files),
            "bytes": sum(item["bytes"] for item in files),
            "by_scope": dict(Counter(item["scope"] for item in files)),
            "by_category": dict(Counter(item["category"] for item in files)),
            "previous_backups": len(previous),
        },
        "database": {
            "source_path": "data/ads_intel.db",
            "restored_as": "data/ads_intel.db",
            "snapshot_method": "sqlite3 backup API",
        },
        "excluded": {
            "previous_backups": excluded,
            "secrets": sorted(name for name in SECRET_NAMES),
            "directories": sorted(EXCLUDED_DIR_NAMES),
            "transient_suffixes": list(TRANSIENT_SUFFIXES),
        },
    }


def _snapshot_database(db_path: Path, destination: Path) -> None:
    source = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def create_recovery_backup(
    root: Path,
    destination: Path,
    *,
    manifest_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest_dir = (manifest_dir or root / "data" / "manifests").resolve()
    manifest_dir.mkdir(parents=True, exist_ok=True)
    db_path = (db_path or DEFAULT_DB_PATH).resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}")

    code = build_code_inventory(root)
    data = build_data_inventory(root)
    recovery = build_recovery_manifest(root)
    code_path = manifest_dir / f"code_inventory_{stamp}.json"
    data_path = manifest_dir / f"data_inventory_{stamp}.json"
    recovery_path = manifest_dir / f"recovery_manifest_{stamp}.json"
    write_json(code_path, code)
    write_json(data_path, data)
    write_json(recovery_path, recovery)

    archive_path = destination / f"phase2_recovery_{stamp}.zip"
    counter = 1
    while archive_path.exists():
        archive_path = destination / f"phase2_recovery_{stamp}_{counter}.zip"
        counter += 1

    with tempfile.TemporaryDirectory(prefix="phase2_snapshot_") as temporary:
        snapshot_path = Path(temporary) / "ads_intel.db"
        _snapshot_database(db_path, snapshot_path)
        snapshot_sha = sha256_file(snapshot_path)
        snapshot_bytes = snapshot_path.stat().st_size
        recovery["database"].update(
            {
                "sha256": snapshot_sha,
                "bytes": snapshot_bytes,
                "snapshot_generated_at": utc_now(),
            }
        )
        write_json(recovery_path, recovery)
        code_sha = sha256_file(code_path)
        data_sha = sha256_file(data_path)
        recovery_sha = sha256_file(recovery_path)
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for entry in recovery["files"]:
                archive.write(root / entry["path"], arcname=entry["path"])
            archive.write(snapshot_path, arcname="data/ads_intel.db")
            for path in (code_path, data_path, recovery_path):
                archive.write(path, arcname=path.relative_to(root).as_posix())
        archive_sha = sha256_file(archive_path)

    report = {
        "schema": "recovery-restore-report-v1",
        "generated_at": utc_now(),
        "ok": False,
        "archive": archive_path.relative_to(root).as_posix(),
        "archive_sha256": archive_sha,
        "archive_bytes": archive_path.stat().st_size,
        "manifests": {
            "code": {
                "path": code_path.relative_to(root).as_posix(),
                "sha256": code_sha,
            },
            "data": {
                "path": data_path.relative_to(root).as_posix(),
                "sha256": data_sha,
            },
            "recovery": {
                "path": recovery_path.relative_to(root).as_posix(),
                "sha256": recovery_sha,
            },
        },
        "database": {
            "source_sha256": sha256_file(db_path),
            "snapshot_sha256": snapshot_sha,
            "snapshot_bytes": snapshot_bytes,
        },
        "missing": [],
        "mismatch": [],
        "extra": [],
        "integrity": None,
        "foreign_keys": None,
        "counts": {
            "recovery_files": len(recovery["files"]),
            "code_files": code["counts"]["files"],
            "data_files": data["counts"]["files"],
        },
    }

    with tempfile.TemporaryDirectory(prefix="phase2_restore_") as temporary:
        restore_root = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            bad = archive.testzip()
            if bad is not None:
                report["mismatch"].append(f"zip test failed: {bad}")
            archive.extractall(restore_root)
        for entry in recovery["files"]:
            restored = restore_root / entry["path"]
            if not restored.is_file():
                report["missing"].append(entry["path"])
            elif sha256_file(restored) != entry["sha256"]:
                report["mismatch"].append(entry["path"])
        restored_db = restore_root / "data" / "ads_intel.db"
        if not restored_db.is_file():
            report["missing"].append("data/ads_intel.db")
        elif sha256_file(restored_db) != snapshot_sha:
            report["mismatch"].append("data/ads_intel.db")
        control = [code_path, data_path, recovery_path]
        allowed = {entry["path"] for entry in recovery["files"]}
        allowed.add("data/ads_intel.db")
        for path in control:
            relative = path.relative_to(root).as_posix()
            allowed.add(relative)
            restored = restore_root / relative
            if not restored.is_file() or sha256_file(restored) != sha256_file(path):
                report["mismatch"].append(relative)
        extracted = {
            path.relative_to(restore_root).as_posix()
            for path in restore_root.rglob("*")
            if path.is_file()
        }
        report["extra"] = sorted(extracted - allowed)
        if restored_db.is_file():
            connection = sqlite3.connect(f"file:{restored_db.as_posix()}?mode=ro", uri=True)
            try:
                report["integrity"] = connection.execute("PRAGMA integrity_check").fetchone()[0]
                report["foreign_keys"] = list(
                    connection.execute("PRAGMA foreign_key_check").fetchall()
                )
                report["counts"]["restored_tables"] = {
                    row[0]: connection.execute(
                        f'SELECT COUNT(*) FROM "{row[0]}"'
                    ).fetchone()[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                    )
                }
            finally:
                connection.close()
    report["ok"] = (
        not report["missing"]
        and not report["mismatch"]
        and not report["extra"]
        and report["integrity"] == "ok"
        and not report["foreign_keys"]
    )
    report_path = manifest_dir / f"recovery_restore_report_{stamp}.json"
    write_json(report_path, report)
    report["report_path"] = report_path.relative_to(root).as_posix()
    return report


def restore_recovery_backup(archive_path: Path, target: Path) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt archive entry: {bad}")
        archive.extractall(target)
    names = sorted(
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    )
    return {"target": str(target), "archive": str(archive_path), "files": names}
