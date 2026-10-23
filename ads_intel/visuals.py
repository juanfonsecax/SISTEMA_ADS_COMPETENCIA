from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover - exercised only when dependency is absent
    raise RuntimeError(
        "Phase 2 visual similarity requires Pillow. Install with: "
        "python -m pip install -r requirements.txt"
    ) from exc

from .config import DEFAULT_THUMBNAIL_DIR
from .util import canonical_json, normalize_relpath, sha256_file, utc_now

METHOD = "dhash"
METHOD_VERSION = "1"
HASH_BITS = 64
DEFAULT_THRESHOLD = 8
THUMBNAIL_MAX_SIZE = 320


def _image_hash(image: Image.Image) -> str:
    grayscale = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(grayscale.tobytes())
    value = 0
    bit = 0
    for row in range(8):
        offset = row * 9
        for column in range(8):
            if pixels[offset + column] > pixels[offset + column + 1]:
                value |= 1 << bit
            bit += 1
    return f"{value:016x}"


def dhash64(path: Path) -> tuple[str, int, int]:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        return _image_hash(image), int(width), int(height)


def hamming_distance(left: str, right: str) -> int:
    if len(left) != 16 or len(right) != 16:
        raise ValueError("Perceptual hashes must be 16-character hexadecimal strings")
    return (int(left, 16) ^ int(right, 16)).bit_count()


def _save_thumbnail(path: Path, root: Path, thumbnail_root: Path, sha256: str) -> str:
    destination = thumbnail_root / METHOD / METHOD_VERSION / sha256[:2] / f"{sha256}.jpg"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE), Image.Resampling.LANCZOS)
        image.save(destination, format="JPEG", quality=85, optimize=True)
    try:
        return normalize_relpath(root, destination)
    except ValueError:
        return str(destination)


def _failure_item(
    connection: sqlite3.Connection,
    asset_id: int,
    storage_key: str,
    message: str,
    now: str,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO review_item
            (item_key, category, object_type, object_id, title, description,
             evidence_json, status, created_at, updated_at)
        VALUES (?, 'visual', 'asset', ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            f"visual:failed:{asset_id}",
            asset_id,
            f"Visual scan failed for asset {asset_id}",
            "The image could not be processed. The original asset is unchanged and requires review.",
            canonical_json({"asset_id": asset_id, "storage_key": storage_key, "error": message}),
            now,
            now,
        ),
    )


def _previous_review_status(
    connection: sqlite3.Connection,
    left_asset_id: int,
    right_asset_id: int,
    run_id: int,
) -> str:
    row = connection.execute(
        """
        SELECT review_status
        FROM visual_similarity_candidate
        WHERE left_asset_id = ? AND right_asset_id = ?
          AND method = ? AND method_version = ? AND scan_run_id < ?
        ORDER BY scan_run_id DESC
        LIMIT 1
        """,
        (left_asset_id, right_asset_id, METHOD, METHOD_VERSION, run_id),
    ).fetchone()
    return str(row["review_status"]) if row is not None else "pending"


def scan_visual_similarity(
    connection: sqlite3.Connection,
    root: Path,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    thumbnail_root: Path | None = None,
) -> dict[str, Any]:
    if not 0 <= threshold <= HASH_BITS:
        raise ValueError("Threshold must be between 0 and 64")
    root = root.resolve()
    thumbs = (thumbnail_root or DEFAULT_THUMBNAIL_DIR).resolve()
    started = utc_now()
    cursor = connection.execute(
        """
        INSERT INTO visual_scan_run
            (method, method_version, threshold, started_at, status)
        VALUES (?, ?, ?, ?, 'running')
        """,
        (METHOD, METHOD_VERSION, threshold, started),
    )
    run_id = int(cursor.lastrowid)
    connection.commit()
    assets = connection.execute(
        "SELECT id, storage_key, sha256 FROM asset WHERE asset_type = 'image' ORDER BY id"
    ).fetchall()
    processed = 0
    failures: list[dict[str, Any]] = []
    now = utc_now()
    try:
        with connection:
            for asset in assets:
                asset_id = int(asset["id"])
                path = root / asset["storage_key"]
                if not path.is_file():
                    message = f"Missing image file: {asset['storage_key']}"
                    failures.append({"asset_id": asset_id, "error": message})
                    _failure_item(connection, asset_id, asset["storage_key"], message, now)
                    continue
                actual_sha = sha256_file(path)
                if actual_sha != asset["sha256"]:
                    message = "Source SHA-256 differs from the imported asset; signature not overwritten"
                    failures.append({"asset_id": asset_id, "error": message})
                    _failure_item(connection, asset_id, asset["storage_key"], message, now)
                    continue
                try:
                    hash_hex, width, height = dhash64(path)
                    thumbnail_key = _save_thumbnail(path, root, thumbs, actual_sha)
                except Exception as exc:  # Pillow reports different decoder errors
                    message = f"{type(exc).__name__}: {exc}"
                    failures.append({"asset_id": asset_id, "error": message})
                    _failure_item(connection, asset_id, asset["storage_key"], message, now)
                    continue
                connection.execute(
                    """
                    INSERT INTO asset_visual_signature
                        (asset_id, method, method_version, hash_hex, hash_bits, width, height,
                         thumbnail_key, source_sha256, computed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(asset_id, method, method_version) DO UPDATE SET
                        hash_hex = excluded.hash_hex,
                        hash_bits = excluded.hash_bits,
                        width = excluded.width,
                        height = excluded.height,
                        thumbnail_key = excluded.thumbnail_key,
                        source_sha256 = excluded.source_sha256,
                        computed_at = excluded.computed_at
                    """,
                    (
                        asset_id,
                        METHOD,
                        METHOD_VERSION,
                        hash_hex,
                        HASH_BITS,
                        width,
                        height,
                        thumbnail_key,
                        actual_sha,
                        now,
                    ),
                )
                connection.execute(
                    "UPDATE asset SET perceptual_hash = ? WHERE id = ?",
                    (hash_hex, asset_id),
                )
                processed += 1

            signatures = connection.execute(
                """
                SELECT s.asset_id, s.hash_hex, s.source_sha256, a.width, a.height
                FROM asset_visual_signature s
                JOIN asset a ON a.id = s.asset_id
                WHERE s.method = ? AND s.method_version = ?
                ORDER BY s.asset_id
                """,
                (METHOD, METHOD_VERSION),
            ).fetchall()
            candidate_count = 0
            exact_sha_matches = 0
            for index, left in enumerate(signatures):
                for right in signatures[index + 1 :]:
                    distance = hamming_distance(left["hash_hex"], right["hash_hex"])
                    if distance > threshold:
                        continue
                    exact_sha_match = left["source_sha256"] == right["source_sha256"]
                    if exact_sha_match:
                        exact_sha_matches += 1
                    left_id = int(left["asset_id"])
                    right_id = int(right["asset_id"])
                    pair_left = min(left_id, right_id)
                    pair_right = max(left_id, right_id)
                    previous_status = _previous_review_status(
                        connection, pair_left, pair_right, run_id
                    )
                    connection.execute(
                        """
                        INSERT INTO visual_similarity_candidate
                            (scan_run_id, left_asset_id, right_asset_id, method, method_version,
                             distance, threshold, review_status, evidence_json, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(scan_run_id, left_asset_id, right_asset_id, method, method_version)
                        DO UPDATE SET
                            distance = excluded.distance,
                            threshold = excluded.threshold,
                            evidence_json = excluded.evidence_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            run_id,
                            pair_left,
                            pair_right,
                            METHOD,
                            METHOD_VERSION,
                            distance,
                            threshold,
                            previous_status,
                            canonical_json(
                                {
                                    "distance": distance,
                                    "threshold": threshold,
                                    "scan_run_id": run_id,
                                    "method": METHOD,
                                    "method_version": METHOD_VERSION,
                                    "left_sha256": left["source_sha256"],
                                    "right_sha256": right["source_sha256"],
                                    "exact_sha256_match": exact_sha_match,
                                    "left_size": [left["width"], left["height"]],
                                    "right_size": [right["width"], right["height"]],
                                    "duplicate_claim": False,
                                }
                            ),
                            now,
                            now,
                        ),
                    )
                    candidate_count += 1

            counts = {
                "assets": len(assets),
                "processed": processed,
                "failed": len(failures),
                "signatures": len(signatures),
                "candidates": candidate_count,
                "exact_sha_matches": exact_sha_matches,
            }
            connection.execute(
                """
                UPDATE visual_scan_run
                SET finished_at = ?, status = ?, counts_json = ?, errors_json = ?
                WHERE id = ?
                """,
                (
                    utc_now(),
                    "completed" if not failures else "completed_with_errors",
                    canonical_json(counts),
                    canonical_json(failures) if failures else None,
                    run_id,
                ),
            )
        return {
            "run_id": run_id,
            "method": METHOD,
            "method_version": METHOD_VERSION,
            "threshold": threshold,
            "thumbnail_root": str(thumbs),
            **counts,
            "errors": failures,
        }
    except Exception:
        connection.execute(
            "UPDATE visual_scan_run SET finished_at = ?, status = 'failed' WHERE id = ?",
            (utc_now(), run_id),
        )
        connection.commit()
        raise


def latest_visual_scan_run(
    connection: sqlite3.Connection,
    *,
    method: str = METHOD,
    method_version: str = METHOD_VERSION,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT *
        FROM visual_scan_run
        WHERE method = ? AND method_version = ?
          AND status IN ('completed', 'completed_with_errors')
        ORDER BY id DESC
        LIMIT 1
        """,
        (method, method_version),
    ).fetchone()
    return dict(row) if row is not None else None


def list_visual_scan_runs(
    connection: sqlite3.Connection,
    *,
    method: str = METHOD,
    method_version: str = METHOD_VERSION,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    sql = """
        SELECT r.*,
               (SELECT COUNT(*) FROM visual_similarity_candidate c
                WHERE c.scan_run_id = r.id) AS candidate_count
        FROM visual_scan_run r
        WHERE r.method = ? AND r.method_version = ?
        ORDER BY r.id DESC
    """
    parameters: list[Any] = [method, method_version]
    if limit is not None:
        sql += " LIMIT ?"
        parameters.append(limit)
    return [dict(row) for row in connection.execute(sql, parameters)]


def list_visual_candidates(
    connection: sqlite3.Connection,
    *,
    run_id: int | None = None,
    threshold: int | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    if run_id is None:
        run = latest_visual_scan_run(connection)
        if run is None:
            return []
        selected_run_id = int(run["id"])
        method = str(run["method"])
        method_version = str(run["method_version"])
    else:
        run = connection.execute(
            "SELECT * FROM visual_scan_run WHERE id = ?",
            (run_id,),
        ).fetchone()
        if run is None:
            raise ValueError(f"Unknown visual scan run: {run_id}")
        selected_run_id = int(run["id"])
        method = str(run["method"])
        method_version = str(run["method_version"])
    clauses = [
        "c.scan_run_id = ?",
        "c.method = ?",
        "c.method_version = ?",
    ]
    parameters: list[Any] = [selected_run_id, method, method_version]
    if threshold is not None:
        clauses.append("c.distance <= ?")
        parameters.append(threshold)
    sql = f"""
        SELECT c.id, c.scan_run_id, c.left_asset_id, c.right_asset_id, c.distance,
               c.threshold, c.review_status, c.evidence_json, a.storage_key AS left_key,
               b.storage_key AS right_key, r.threshold AS run_threshold,
               r.status AS run_status, r.finished_at AS run_finished_at
        FROM visual_similarity_candidate c
        JOIN asset a ON a.id = c.left_asset_id
        JOIN asset b ON b.id = c.right_asset_id
        JOIN visual_scan_run r ON r.id = c.scan_run_id
        WHERE {' AND '.join(clauses)}
        ORDER BY c.distance, c.left_asset_id, c.right_asset_id
    """
    if limit is not None:
        sql += " LIMIT ?"
        parameters.append(limit)
    return [dict(row) for row in connection.execute(sql, parameters)]
