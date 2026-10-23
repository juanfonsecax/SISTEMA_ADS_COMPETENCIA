from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import (
    AD_FILES,
    LEGACY_BACKUP_GLOBS,
    LEGACY_RAW_GLOBS,
)
from .jpeg import is_jpeg, jpeg_dimensions
from .util import (
    git_head,
    git_tracked_files,
    git_untracked_files,
    iter_glob_files,
    md5_file,
    normalize_relpath,
    read_csv_rows,
    read_json,
    sha256_bytes,
    sha256_file,
    utc_now,
    write_json,
)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width > 0 and height > 0:
        return width, height
    return None


def _image_metadata(root: Path, path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    width: int | None = None
    height: int | None = None
    if is_jpeg(data):
        dimensions = jpeg_dimensions(data)
        if dimensions:
            width, height = dimensions
    elif path.suffix.lower() == ".png":
        dimensions = _png_dimensions(data)
        if dimensions:
            width, height = dimensions
    return {
        "path": normalize_relpath(root, path),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "md5": md5_file(path),
        "mime_type": _mime_type(path),
        "width": width,
        "height": height,
        "is_jpeg": is_jpeg(data),
    }


def _classify_legacy_file(path: str) -> str:
    name = Path(path).name
    if name in AD_FILES:
        return "ad_file"
    if name == "_PAGINAS.csv":
        return "page_file"
    if name in {"_CLASIF_FAVORITOS.csv", "_ETIQUETAS_MANUALES.csv"}:
        return "tag_file"
    if name in {"_PRECLASIFICACION.csv", "_COPIES.csv"}:
        return "copy_or_classification_file"
    if name in {"_SELECCION_EXTRACCION.csv", "_ELEMENTOS.csv"}:
        return "selection_file"
    if path.startswith("_BLUEPRINTS/") and path.endswith(".json"):
        return "blueprint_json"
    if name.endswith(".py") or name.endswith(".js"):
        return "script"
    if name.endswith(".md") or name.endswith(".txt"):
        return "document"
    return "legacy_file"


def _count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    return len(read_csv_rows(path))


def _unique_values(path: Path, key: str) -> int:
    if not path.exists():
        return 0
    return len({row.get(key, "").strip() for row in read_csv_rows(path) if row.get(key, "").strip()})


def _category_for_path(path: str) -> str:
    if path == ".gitignore":
        return "config"
    if path.startswith("_IMG/"):
        return "image"
    if path.startswith("_BANCO_CREATIVOS/"):
        if path.endswith(".csv"):
            return "reference_index"
        if path.endswith(".md"):
            return "reference_document"
        return "reference_asset"
    if path.startswith("_RAW/"):
        return "raw_capture"
    if path.startswith("ANALISIS/"):
        return "research"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("odd/"):
        return "governance"
    if path.startswith("ads_intel/"):
        return "code"
    if path.startswith("_BLUEPRINTS/"):
        if path.endswith((".json", ".csv")) or "/FICHAS/" in path or "/CANONICOS/" in path:
            return "blueprint_or_ficha"
        return "blueprint_source"
    if path.endswith((".py", ".js")):
        return "legacy_code"
    if path.endswith((".html", ".css", ".js")):
        return "generated_view"
    if path.endswith((".md", ".txt")):
        return "documentation"
    return "source_data"


def _candidate_paths(root: Path) -> list[Path]:
    tracked = git_tracked_files(root)
    untracked = git_untracked_files(root)
    if tracked or untracked:
        return tracked + untracked
    ignored = (".git/", "data/", "__pycache__/")
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and not normalize_relpath(root, path).startswith(ignored)
        and path.suffix.lower() not in {".pyc", ".pyo"}
    ]


def build_manifest(root: Path, include_images: bool = True) -> dict[str, Any]:
    tracked_paths = {path.resolve() for path in git_tracked_files(root)}
    candidate_paths = _candidate_paths(root)
    deduped: dict[str, Path] = {}
    for path in candidate_paths:
        if path.exists():
            deduped[normalize_relpath(root, path)] = path

    files = []
    images = []
    reference_assets = []
    for key in sorted(deduped):
        path = deduped[key]
        scope = "tracked" if path.resolve() in tracked_paths else "untracked"
        if key.startswith("_IMG/") and path.suffix.lower() in IMAGE_SUFFIXES:
            if include_images:
                item = _image_metadata(root, path)
                item.update({"scope": scope, "category": "image"})
                images.append(item)
            continue
        if key.startswith("_BANCO_CREATIVOS/") and path.suffix.lower() in IMAGE_SUFFIXES:
            item = _image_metadata(root, path)
            item.update({"scope": scope, "category": "reference_asset"})
            reference_assets.append(item)
            continue
        files.append(
            {
                "path": key,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "kind": _classify_legacy_file(key),
                "category": _category_for_path(key),
                "scope": scope,
            }
        )

    ficha_manifest = root / "_BLUEPRINTS" / "FICHAS" / "_MANIFIESTO.csv"
    refs_index = root / "_BANCO_CREATIVOS" / "_INDICE.csv"
    total = len(files) + len(images) + len(reference_assets)
    tracked_total = sum(
        1 for item in files + images + reference_assets if item["scope"] == "tracked"
    )
    untracked_total = total - tracked_total
    by_category: dict[str, int] = {}
    for item in files + images + reference_assets:
        category = item["category"]
        by_category[category] = by_category.get(category, 0) + 1
    counts = {
        "files": len(files),
        "images": len(images),
        "reference_assets": len(reference_assets),
        "tracked": tracked_total,
        "untracked": untracked_total,
        "tracked_total": tracked_total,
        "total": total,
        "total_bytes": sum(item["bytes"] for item in files + images + reference_assets),
        "image_bytes": sum(item["bytes"] for item in images),
        "reference_bytes": sum(item["bytes"] for item in reference_assets),
        "images_with_dimensions": sum(1 for item in images if item["width"] and item["height"]),
        "by_category": by_category,
        "ads_rows": sum(_count_csv(root / name) for name in AD_FILES),
        "ads_unique": len(
            {
                row.get("ad_archive_id", "").strip()
                for name in AD_FILES
                for row in read_csv_rows(root / name)
                if row.get("ad_archive_id", "").strip()
            }
        ),
        "pages_rows": _count_csv(root / "_PAGINAS.csv"),
        "pages_unique": _unique_values(root / "_PAGINAS.csv", "page_id"),
        "favorites_rows": _count_csv(root / "_CLASIF_FAVORITOS.csv"),
        "gallery_tags_rows": _count_csv(root / "_ETIQUETAS_MANUALES.csv"),
        "preclassification_rows": _count_csv(root / "_PRECLASIFICACION.csv"),
        "copies_rows": _count_csv(root / "_COPIES.csv"),
        "selection_rows": _count_csv(root / "_SELECCION_EXTRACCION.csv"),
        "element_rows": _count_csv(root / "_ELEMENTOS.csv"),
        "reference_rows": _count_csv(refs_index),
        "ficha_rows": _count_csv(ficha_manifest),
        "canonical_json": len(list((root / "_BLUEPRINTS" / "CANONICOS").glob("*.json"))),
        "blueprint_json": len(list((root / "_BLUEPRINTS").glob("blueprint_*.json"))),
        "filled_blueprint_json": len(list((root / "_BLUEPRINTS").glob("LLENO_T01_*.json"))),
    }
    return {
        "schema": "legacy-manifest-v2",
        "generated_at": utc_now(),
        "repo_head": git_head(root),
        "root_name": root.name,
        "files": files,
        "images": images,
        "reference_assets": reference_assets,
        "counts": counts,
    }


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    write_json(path, manifest)


def create_backup(
    root: Path,
    destination: Path,
    manifest_path: Path | None = None,
    include_images: bool = False,
    manifest: dict[str, Any] | None = None,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = destination / f"legacy_snapshot_{stamp}.zip"
    counter = 1
    while archive_path.exists():
        archive_path = destination / f"legacy_snapshot_{stamp}_{counter}.zip"
        counter += 1
    if manifest is None and manifest_path and manifest_path.exists():
        manifest = read_json(manifest_path)
    if manifest:
        relative_paths = [item["path"] for item in manifest.get("files", [])]
        relative_paths.extend(item["path"] for item in manifest.get("reference_assets", []))
        if include_images:
            relative_paths.extend(item["path"] for item in manifest.get("images", []))
        paths = [root / relative for relative in relative_paths if (root / relative).is_file()]
    else:
        paths = iter_glob_files(root, LEGACY_BACKUP_GLOBS + LEGACY_RAW_GLOBS)
    unique: dict[str, Path] = {normalize_relpath(root, path): path for path in paths}
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(unique):
            path = unique[relative]
            if relative.startswith((".git/", "data/", "__pycache__/")):
                continue
            if relative.startswith("_IMG/") and not include_images:
                continue
            if path.suffix.lower() in {".pyc", ".pyo", ".db", ".db-wal", ".db-shm"}:
                continue
            archive.write(path, arcname=relative)
        if manifest_path and manifest_path.exists():
            archive.write(manifest_path, arcname="legacy_manifest.json")
    return archive_path


def freeze(
    root: Path,
    manifest_path: Path,
    backup_dir: Path,
    include_images: bool = True,
    do_backup: bool = True,
) -> dict[str, Any]:
    manifest = build_manifest(root, include_images=include_images)
    write_manifest(manifest, manifest_path)
    backup_path = (
        create_backup(root, backup_dir, manifest_path, include_images=include_images, manifest=manifest)
        if do_backup
        else None
    )
    return {
        "manifest_path": str(manifest_path),
        "backup_path": str(backup_path) if backup_path else None,
        "counts": manifest["counts"],
    }
