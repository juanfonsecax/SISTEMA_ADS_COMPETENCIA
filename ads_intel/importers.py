from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from .config import (
    AD_FILES,
    CATALOG_CONCEPTS,
    GALLERY_CONCEPTS,
    PRECLASSIFICATION_CONCEPTS,
    SOURCE_NAME,
    SOURCE_PERMISSION_BASIS,
    SOURCE_TYPE,
)
from .db import apply_migrations, connect
from .jpeg import jpeg_dimensions
from .util import (
    as_float,
    as_int,
    as_text,
    canonical_json,
    date_to_utc,
    md5_file,
    normalize_relpath,
    parse_date,
    read_csv_rows,
    read_json,
    sha256_file,
    sha256_text,
    utc_now,
)

CATALOG_KEY_BY_NUMBER = {
    "C1": "C1_OFERTA",
    "C2": "C2_BENEFICIOS",
    "C3": "C3_SINTOMA",
    "C4": "C4_TRANSFORMACION",
    "C5": "C5_PRUEBA",
    "C7": "C7_DESEO",
    "C8": "C8_PROGRESION",
    "C9": "C9_COMPARACION",
}

DEFAULT_DATES = {"_ADS.csv": "2026-08-17", "_BANCO.csv": "2026-08-18"}


class LegacyImporter:
    def __init__(self, connection, root: Path) -> None:
        self.connection = connection
        self.root = root
        self.now = utc_now()
        self.source_id: int | None = None
        self.counts: Counter[str] = Counter()
        self.tag_cache: dict[tuple[str, str], int] = {}
        self.batches: dict[tuple[str, str], int] = {}
        self.by_ad_id: dict[str, int] = {}
        self.by_archivo: dict[str, int] = {}
        self.selection_ad_ids: dict[int, int | None] = {}
        self.catalog_definitions: dict[str, tuple[str, str]] = {}

    def run(self) -> dict[str, int]:
        self.source_id = self._ensure_source()
        self._import_pages()
        self._import_ads()
        self._import_copies()
        self._import_ranking()
        self._import_catalog()
        self._import_preclassification()
        self._import_favorites()
        self._import_gallery_tags()
        self._import_selection()
        self._import_elements()
        self._import_reference_index()
        self._import_fichas()
        self._import_canonical()
        self._import_blueprints()
        self._import_product()
        self._import_summary_issues()
        counts = self._db_counts()
        self._finish_job(counts)
        return self._db_counts()

    def _db_counts(self) -> dict[str, int]:
        from .reconcile import db_counts

        return db_counts(self.connection)

    def _ensure_source(self) -> int:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO source
                (name, source_type, permission_basis, active, created_at, notes)
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (
                SOURCE_NAME,
                SOURCE_TYPE,
                SOURCE_PERMISSION_BASIS,
                self.now,
                "Imported from manually captured Meta Ad Library exports.",
            ),
        )
        row = self.connection.execute("SELECT id FROM source WHERE name = ?", (SOURCE_NAME,)).fetchone()
        if row is None:
            raise RuntimeError("Could not create source")
        return int(row["id"])

    def _ensure_batch(self, legacy_file: str, observed_on: str) -> int:
        key = (legacy_file, observed_on)
        if key in self.batches:
            return self.batches[key]
        self.connection.execute(
            """
            INSERT OR IGNORE INTO capture_batch
                (source_id, legacy_file, observed_on, imported_at, query_config_json, status, notes)
            VALUES (?, ?, ?, ?, ?, 'completed', ?)
            """,
            (
                self.source_id,
                legacy_file,
                observed_on,
                self.now,
                canonical_json({"legacy_file": legacy_file, "country": "GT", "mode": "manual_browser_export"}),
                "Legacy CSV batch; not re-captured by this import.",
            ),
        )
        row = self.connection.execute(
            "SELECT id FROM capture_batch WHERE source_id = ? AND observed_on = ? AND legacy_file = ?",
            (self.source_id, observed_on, legacy_file),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Could not create batch for {legacy_file} {observed_on}")
        batch_id = int(row["id"])
        self.batches[key] = batch_id
        return batch_id

    def _payload(self, legacy_file: str, legacy_row: int, row: dict[str, Any], external_id: str | None = None) -> int:
        raw_json = canonical_json(row)
        raw_hash = sha256_text(raw_json)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO source_payload
                (source_id, external_id, raw_json, raw_hash, legacy_file, legacy_row, fetched_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.source_id,
                external_id,
                raw_json,
                raw_hash,
                legacy_file,
                legacy_row,
                self.now,
                self.now,
            ),
        )
        payload = self.connection.execute(
            "SELECT id FROM source_payload WHERE legacy_file = ? AND legacy_row = ? AND raw_hash = ?",
            (legacy_file, legacy_row, raw_hash),
        ).fetchone()
        if payload is None:
            raise RuntimeError(f"Could not persist payload for {legacy_file}:{legacy_row}")
        return int(payload["id"])

    def _issue(
        self,
        severity: str,
        issue_type: str,
        source_file: str | None,
        source_row: int | None,
        external_id: str | None,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        issue_key = sha256_text(
            "|".join(
                [
                    issue_type,
                    source_file or "",
                    str(source_row or ""),
                    external_id or "",
                    message,
                ]
            )
        )
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO import_issue
                (issue_key, severity, issue_type, source_file, source_row, external_id, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue_key,
                severity,
                issue_type,
                source_file,
                source_row,
                external_id,
                message,
                canonical_json(payload) if payload is not None else None,
                self.now,
            ),
        )
        if cursor.rowcount:
            self.counts["issues"] += 1

    def _ensure_advertiser(
        self,
        page_id: str,
        name: str | None = None,
        page_url: str | None = None,
        country: str | None = None,
        niche: str | None = None,
        active_ads: int | None = None,
        oldest_days: int | None = None,
        legacy_status: str | None = None,
        source_folder: str | None = None,
        last_seen_at: str | None = None,
    ) -> int:
        self.connection.execute(
            """
            INSERT INTO advertiser
                (source_id, external_page_id, name, page_url, country, niche,
                 reported_active_ads, reported_oldest_ad_days, legacy_status,
                 source_folder, first_seen_at, last_seen_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, external_page_id) DO UPDATE SET
                name = COALESCE(advertiser.name, excluded.name),
                page_url = COALESCE(advertiser.page_url, excluded.page_url),
                country = COALESCE(advertiser.country, excluded.country),
                niche = COALESCE(advertiser.niche, excluded.niche),
                reported_active_ads = COALESCE(advertiser.reported_active_ads, excluded.reported_active_ads),
                reported_oldest_ad_days = COALESCE(advertiser.reported_oldest_ad_days, excluded.reported_oldest_ad_days),
                legacy_status = COALESCE(advertiser.legacy_status, excluded.legacy_status),
                source_folder = COALESCE(advertiser.source_folder, excluded.source_folder),
                last_seen_at = CASE
                    WHEN excluded.last_seen_at IS NOT NULL
                     AND (advertiser.last_seen_at IS NULL OR excluded.last_seen_at > advertiser.last_seen_at)
                    THEN excluded.last_seen_at
                    ELSE advertiser.last_seen_at
                END
            """,
            (
                self.source_id,
                page_id,
                name,
                page_url,
                country,
                niche,
                active_ads,
                oldest_days,
                legacy_status,
                source_folder,
                last_seen_at,
                last_seen_at,
                self.now,
            ),
        )
        row = self.connection.execute(
            "SELECT id FROM advertiser WHERE source_id = ? AND external_page_id = ?",
            (self.source_id, page_id),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Could not create advertiser {page_id}")
        return int(row["id"])

    def _add_alias(
        self,
        advertiser_id: int,
        name: str | None,
        source_file: str,
        first_seen_at: str | None,
        last_seen_at: str | None,
    ) -> None:
        clean = as_text(name)
        if clean is None:
            return
        canonical = self.connection.execute(
            "SELECT name FROM advertiser WHERE id = ?", (advertiser_id,)
        ).fetchone()
        if canonical is not None and canonical["name"] == clean:
            return
        self.connection.execute(
            """
            INSERT INTO advertiser_alias (advertiser_id, name, first_seen_at, last_seen_at, source_file)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(advertiser_id, name) DO UPDATE SET
                first_seen_at = COALESCE(advertiser_alias.first_seen_at, excluded.first_seen_at),
                last_seen_at = CASE
                    WHEN excluded.last_seen_at IS NOT NULL
                     AND (advertiser_alias.last_seen_at IS NULL OR excluded.last_seen_at > advertiser_alias.last_seen_at)
                    THEN excluded.last_seen_at
                    ELSE advertiser_alias.last_seen_at
                END
            """,
            (advertiser_id, clean, first_seen_at, last_seen_at, source_file),
        )

    def _import_pages(self) -> None:
        path = self.root / "_PAGINAS.csv"
        for index, row in enumerate(read_csv_rows(path)):
            page_id = as_text(row.get("page_id"))
            if page_id is None:
                self._issue("error", "missing_page_id", "_PAGINAS.csv", index + 2, None, "Page row has no page_id", row)
                continue
            name = as_text(row.get("nombre"))
            advertiser_id = self._ensure_advertiser(
                page_id=page_id,
                name=name,
                page_url=as_text(row.get("url_adlibrary")),
                country=as_text(row.get("pais_original")),
                niche=as_text(row.get("nicho")),
                active_ads=as_int(row.get("n_ads_activos")),
                oldest_days=as_int(row.get("ad_mas_antiguo_dias")),
                legacy_status=as_text(row.get("estado")),
                source_folder=as_text(row.get("carpeta_origen")),
                last_seen_at=date_to_utc(parse_date(row.get("fecha_scrape")) or "1970-01-01"),
            )
            self._add_alias(
                advertiser_id,
                name,
                "_PAGINAS.csv",
                date_to_utc(parse_date(row.get("fecha_scrape")) or "1970-01-01"),
                None,
            )
            if name is None:
                self._issue(
                    "warning",
                    "missing_advertiser_name",
                    "_PAGINAS.csv",
                    index + 2,
                    page_id,
                    "Advertiser row has no name; page retained without a canonical name",
                    row,
                )

    def _import_ads(self) -> None:
        for legacy_file in AD_FILES:
            path = self.root / legacy_file
            rows = read_csv_rows(path)
            default_date = DEFAULT_DATES[legacy_file]
            observed_dates = sorted(
                {
                    parse_date(row.get("fecha_cosecha")) or default_date
                    for row in rows
                }
            )
            for observed_on in observed_dates:
                self._ensure_batch(legacy_file, observed_on)

            for index, row in enumerate(rows):
                legacy_row = index + 2
                ad_id = as_text(row.get("ad_archive_id"))
                page_id = as_text(row.get("page_id"))
                if ad_id is None or page_id is None:
                    self._issue(
                        "error",
                        "missing_ad_id_or_page_id",
                        legacy_file,
                        legacy_row,
                        ad_id,
                        "Ad row is missing ad_archive_id or page_id",
                        row,
                    )
                    continue
                observed_on = parse_date(row.get("fecha_cosecha")) or default_date
                observed_at = date_to_utc(observed_on)
                batch_id = self._ensure_batch(legacy_file, observed_on)
                advertiser_name = as_text(row.get("anunciante"))
                advertiser_id = self._ensure_advertiser(
                    page_id=page_id,
                    name=advertiser_name,
                    last_seen_at=observed_at,
                )
                self._add_alias(advertiser_id, advertiser_name, legacy_file, observed_at, observed_at)
                payload_id = self._payload(legacy_file, legacy_row, row, ad_id)

                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO ad_creative
                        (source_id, external_ad_id, advertiser_id, first_seen_at, last_seen_at,
                         canonical_hash, review_state, is_catalog, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'imported', 0, ?, ?)
                    """,
                    (
                        self.source_id,
                        ad_id,
                        advertiser_id,
                        observed_at,
                        observed_at,
                        sha256_text(f"{SOURCE_NAME}:{ad_id}"),
                        self.now,
                        self.now,
                    ),
                )
                creative = self.connection.execute(
                    "SELECT id FROM ad_creative WHERE source_id = ? AND external_ad_id = ?",
                    (self.source_id, ad_id),
                ).fetchone()
                if creative is None:
                    raise RuntimeError(f"Could not create ad_creative {ad_id}")
                creative_id = int(creative["id"])
                self.by_ad_id[ad_id] = creative_id
                self.connection.execute(
                    """
                    UPDATE ad_creative
                    SET first_seen_at = CASE
                            WHEN first_seen_at IS NULL OR ? < first_seen_at THEN ? ELSE first_seen_at END,
                        last_seen_at = CASE
                            WHEN last_seen_at IS NULL OR ? > last_seen_at THEN ? ELSE last_seen_at END,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (observed_at, observed_at, observed_at, observed_at, self.now, creative_id),
                )

                archivo = as_text(row.get("archivo"))
                if archivo:
                    self.by_archivo[archivo] = creative_id
                    self._import_asset(creative_id, archivo, legacy_file, legacy_row, row, ad_id)

                observed_rank = as_int(row.get("rank_impresiones") or row.get("pos"))
                observed_total = as_int(row.get("total_pos"))
                active_days = as_int(row.get("dias_corriendo"))
                page_active = as_int(row.get("ads_activos_pagina"))
                page_oldest = as_int(row.get("ad_mas_viejo_pagina"))
                collation = as_int(row.get("collation_count") or row.get("replicas"))
                same_image = as_int(row.get("replicas_misma_imagen"))
                quadrant = as_text(row.get("cuadrante"))
                velocity = as_float(row.get("velocidad")) if legacy_file == "_ADS.csv" else None

                cursor = self.connection.execute(
                    """
                    INSERT OR IGNORE INTO ad_observation
                        (ad_creative_id, batch_id, observed_on, observed_at, reported_status,
                         active_days_reported, observed_rank, observed_total,
                         page_active_ads_reported, page_oldest_ad_days_reported,
                         reported_collation_count, computed_same_image_count,
                         quadrant_legacy, source_payload_id, reported_velocity, created_at)
                    VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        creative_id,
                        batch_id,
                        observed_on,
                        observed_at,
                        active_days,
                        observed_rank,
                        observed_total,
                        page_active,
                        page_oldest,
                        collation,
                        same_image,
                        quadrant,
                        payload_id,
                        velocity,
                        self.now,
                    ),
                )
                if cursor.rowcount:
                    self.counts["observations"] += 1

                if legacy_file == "_ADS.csv":
                    self._insert_copy(
                        creative_id=creative_id,
                        primary_text=as_text(row.get("copy")),
                        headline=None,
                        description=None,
                        cta=None,
                        destination=None,
                        extraction_method="legacy_ads_copy",
                        source_file=legacy_file,
                        source_row=legacy_row,
                        payload_id=payload_id,
                        is_canonical=True,
                    )
                else:
                    self._insert_copy(
                        creative_id=creative_id,
                        primary_text=as_text(row.get("texto_principal")),
                        headline=as_text(row.get("titulo")),
                        description=as_text(row.get("descripcion")),
                        cta=as_text(row.get("cta")),
                        destination=as_text(row.get("destino")),
                        extraction_method="legacy_banco_fields",
                        source_file=legacy_file,
                        source_row=legacy_row,
                        payload_id=payload_id,
                        is_canonical=True,
                    )

    def _import_asset(
        self,
        creative_id: int,
        archivo: str,
        legacy_file: str,
        legacy_row: int,
        row: dict[str, Any],
        ad_id: str,
    ) -> None:
        relative = Path(archivo.replace("\\", "/"))
        path = self.root / relative
        if not path.exists():
            self._issue(
                "error",
                "missing_image",
                legacy_file,
                legacy_row,
                ad_id,
                f"Image path does not exist: {archivo}",
                row,
            )
            return
        data = path.read_bytes()
        width = height = None
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            dimensions = jpeg_dimensions(data)
            if dimensions:
                width, height = dimensions
        mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "application/octet-stream"
        digest = sha256_file(path)
        md5 = md5_file(path)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO asset
                (asset_type, storage_key, source_url, mime_type, sha256, md5,
                 width, height, bytes, rights_status, created_at, updated_at)
            VALUES ('image', ?, NULL, ?, ?, ?, ?, ?, ?, 'unknown', ?, ?)
            """,
            (
                normalize_relpath(self.root, path),
                mime,
                digest,
                md5,
                width,
                height,
                len(data),
                self.now,
                self.now,
            ),
        )
        asset = self.connection.execute(
            "SELECT id FROM asset WHERE sha256 = ?", (digest,)
        ).fetchone()
        if asset is None:
            raise RuntimeError(f"Could not create asset for {archivo}")
        asset_id = int(asset["id"])
        self.connection.execute(
            """
            INSERT OR IGNORE INTO ad_asset (ad_creative_id, asset_id, role, sequence, source_confidence)
            VALUES (?, ?, 'primary', 1, NULL)
            """,
            (creative_id, asset_id),
        )
        if width and height:
            self.connection.execute(
                "UPDATE asset SET width = COALESCE(width, ?), height = COALESCE(height, ?) WHERE id = ?",
                (width, height, asset_id),
            )

    def _insert_copy(
        self,
        creative_id: int,
        primary_text: str | None,
        headline: str | None,
        description: str | None,
        cta: str | None,
        destination: str | None,
        extraction_method: str,
        source_file: str,
        source_row: int,
        payload_id: int | None,
        is_canonical: bool,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO ad_copy
                (ad_creative_id, primary_text, headline, description, cta, destination_url,
                 language, extraction_method, confidence, confidence_label, is_canonical,
                 source_file, source_row, source_payload_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'es', ?, NULL, NULL, ?, ?, ?, ?, ?)
            """,
            (
                creative_id,
                primary_text,
                headline,
                description,
                cta,
                destination,
                extraction_method,
                1 if is_canonical else 0,
                source_file,
                source_row,
                payload_id,
                self.now,
            ),
        )

    def _import_catalog(self) -> None:
        path = self.root / "_CATALOGO_CONCEPTOS.md"
        text = path.read_text(encoding="utf-8")
        self.connection.execute(
            """
            INSERT OR IGNORE INTO reference_document
                (kind, external_key, ad_creative_id, version, payload_json, content_hash,
                 status, source_file, source_row, created_at)
            VALUES ('catalog', 'CATALOGO_CONCEPTOS', NULL, '1', ?, ?, 'imported', ?, 1, ?)
            """,
            (
                canonical_json({"content": text}),
                sha256_text(text),
                normalize_relpath(self.root, path),
                self.now,
            ),
        )
        for match in re.finditer(r"^### (C\d+) [â€”-] ([^\n]+)\n> ([^\n]+)", text, re.MULTILINE):
            key = CATALOG_KEY_BY_NUMBER.get(match.group(1))
            if key:
                self.catalog_definitions[key] = (match.group(2).strip(), match.group(3).strip())
        for key, label in CATALOG_CONCEPTS.items():
            definition = self.catalog_definitions.get(key, (label, None))[1]
            self._tag_definition("concepto", key, label, definition, "_CATALOGO_CONCEPTOS.md")
        for key in GALLERY_CONCEPTS:
            self._tag_definition("legacy_gallery_auto", key, key.replace("_", " ").title(), None, "gen_galeria.py")
        for key in PRECLASSIFICATION_CONCEPTS:
            self._tag_definition(
                "legacy_preclasificacion",
                key,
                key.replace("_", " ").title(),
                None,
                "clasificar_conceptos.py",
            )
        self._tag_definition("curaduria", "FAVORITO", "Favorito", None, "_CLASIF_FAVORITOS.csv")

    def _tag_definition(
        self,
        dimension: str,
        key: str,
        label: str,
        definition: str | None,
        source: str | None,
    ) -> int:
        cache_key = (dimension, key)
        if cache_key in self.tag_cache:
            return self.tag_cache[cache_key]
        self.connection.execute(
            """
            INSERT OR IGNORE INTO tag_definition
                (dimension, tag_key, label, definition, version, active, source, created_at)
            VALUES (?, ?, ?, ?, 1, 1, ?, ?)
            """,
            (dimension, key, label, definition, source, self.now),
        )
        row = self.connection.execute(
            "SELECT id FROM tag_definition WHERE dimension = ? AND tag_key = ? AND version = 1",
            (dimension, key),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Could not create tag definition {dimension}:{key}")
        tag_id = int(row["id"])
        self.tag_cache[cache_key] = tag_id
        return tag_id

    def _tag(
        self,
        creative_id: int,
        dimension: str,
        key: str,
        label: str,
        method: str,
        assigned_by: str,
        review_status: str,
        source_file: str,
        source_row: int | None,
        confidence_label: str | None = None,
        evidence: dict[str, Any] | None = None,
        definition: str | None = None,
    ) -> None:
        definition_id = self._tag_definition(dimension, key, label, definition, source_file)
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO ad_tag
                (ad_creative_id, asset_id, tag_definition_id, confidence, confidence_label,
                 assigned_by, method, model_version, prompt_version, review_status,
                 evidence_json, source_file, source_row, created_at)
            VALUES (?, NULL, ?, NULL, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?)
            """,
            (
                creative_id,
                definition_id,
                confidence_label,
                assigned_by,
                method,
                review_status,
                canonical_json(evidence) if evidence is not None else None,
                source_file,
                source_row,
                self.now,
            ),
        )
        if cursor.rowcount:
            self.counts["tags"] += 1

    def _find_ad(self, ad_id: str | None = None, archivo: str | None = None) -> int | None:
        if ad_id:
            found = self.by_ad_id.get(ad_id)
            if found:
                return found
            row = self.connection.execute(
                "SELECT id FROM ad_creative WHERE source_id = ? AND external_ad_id = ?",
                (self.source_id, ad_id),
            ).fetchone()
            if row:
                return int(row["id"])
        if archivo:
            return self.by_archivo.get(archivo)
        return None

    def _import_preclassification(self) -> None:
        path = self.root / "_PRECLASIFICACION.csv"
        for index, row in enumerate(read_csv_rows(path)):
            ad_id = as_text(row.get("ad_archive_id"))
            creative_id = self._find_ad(ad_id=ad_id, archivo=as_text(row.get("archivo")))
            if creative_id is None:
                self._issue(
                    "error",
                    "preclassification_orphan",
                    "_PRECLASIFICACION.csv",
                    index + 2,
                    ad_id,
                    "Preclassification row does not match an imported ad",
                    row,
                )
                continue
            payload_id = self._payload("_PRECLASIFICACION.csv", index + 2, row, ad_id)
            concept = as_text(row.get("concepto_auto"))
            if concept:
                self._tag(
                    creative_id,
                    "legacy_preclasificacion",
                    concept,
                    concept.replace("_", " ").title(),
                    method="rule_text",
                    assigned_by="clasificar_conceptos.py",
                    review_status="auto",
                    source_file="_PRECLASIFICACION.csv",
                    source_row=index + 2,
                    confidence_label=as_text(row.get("confianza")),
                    evidence={"texto_muestra": as_text(row.get("texto_muestra")), "payload_id": payload_id},
                )
            if as_text(row.get("es_catalogo")) in {"SI", "1"}:
                self.connection.execute("UPDATE ad_creative SET is_catalog = 1 WHERE id = ?", (creative_id,))
            label = as_text(row.get("confianza"))
            if label and "+" in label:
                self._issue(
                    "info",
                    "combined_confidence_label",
                    "_PRECLASIFICACION.csv",
                    index + 2,
                    ad_id,
                    f"Legacy confidence label combines categories: {label}",
                    row,
                )

    def _import_favorites(self) -> None:
        path = self.root / "_CLASIF_FAVORITOS.csv"
        for index, row in enumerate(read_csv_rows(path)):
            ad_id = None
            creative_id = self._find_ad(archivo=as_text(row.get("archivo")))
            if creative_id is None:
                self._issue(
                    "error",
                    "favorite_orphan",
                    "_CLASIF_FAVORITOS.csv",
                    index + 2,
                    None,
                    "Favorite row does not match an imported image",
                    row,
                )
                continue
            payload_id = self._payload("_CLASIF_FAVORITOS.csv", index + 2, row, ad_id)
            final = as_text(row.get("concepto_final"))
            raw = as_text(row.get("concepto_crudo"))
            if final:
                if final not in CATALOG_CONCEPTS:
                    self._issue(
                        "warning",
                        "unknown_final_concept",
                        "_CLASIF_FAVORITOS.csv",
                        index + 2,
                        ad_id,
                        f"Unknown final concept: {final}",
                        row,
                    )
                    final = "SIN_CLASIFICAR"
                self._tag(
                    creative_id,
                    "concepto",
                    final,
                    CATALOG_CONCEPTS[final],
                    method="manual_final",
                    assigned_by="operator",
                    review_status="reviewed",
                    source_file="_CLASIF_FAVORITOS.csv",
                    source_row=index + 2,
                    evidence={"payload_id": payload_id, "concepto_crudo": raw},
                    definition=self.catalog_definitions.get(final, (None, None))[1],
                )
            if raw:
                self._tag(
                    creative_id,
                    "legacy_concepto_crudo",
                    raw,
                    raw,
                    method="manual_raw",
                    assigned_by="operator",
                    review_status="imported",
                    source_file="_CLASIF_FAVORITOS.csv",
                    source_row=index + 2,
                    evidence={"payload_id": payload_id, "concepto_final": as_text(row.get("concepto_final"))},
                )
            self._tag(
                creative_id,
                "curaduria",
                "FAVORITO",
                "Favorito",
                method="manual_curation",
                assigned_by="operator",
                review_status="reviewed",
                source_file="_CLASIF_FAVORITOS.csv",
                source_row=index + 2,
                evidence={"payload_id": payload_id},
            )

    def _import_gallery_tags(self) -> None:
        path = self.root / "_ETIQUETAS_MANUALES.csv"
        for index, row in enumerate(read_csv_rows(path)):
            ad_id = as_text(row.get("ad_archive_id"))
            creative_id = self._find_ad(ad_id=ad_id, archivo=as_text(row.get("archivo")))
            if creative_id is None:
                self._issue(
                    "error",
                    "gallery_tag_orphan",
                    "_ETIQUETAS_MANUALES.csv",
                    index + 2,
                    ad_id,
                    "Gallery tag row does not match an imported ad",
                    row,
                )
                continue
            payload_id = self._payload("_ETIQUETAS_MANUALES.csv", index + 2, row, ad_id)
            concept = as_text(row.get("concepto_auto"))
            if concept:
                self._tag(
                    creative_id,
                    "legacy_gallery_auto",
                    concept,
                    concept.replace("_", " ").title(),
                    method="rule_text_gallery",
                    assigned_by="gen_galeria.py",
                    review_status="auto",
                    source_file="_ETIQUETAS_MANUALES.csv",
                    source_row=index + 2,
                    evidence={"payload_id": payload_id, "favorito": as_text(row.get("favorito"))},
                )
            if as_text(row.get("es_catalogo")) in {"SI", "1"}:
                self.connection.execute("UPDATE ad_creative SET is_catalog = 1 WHERE id = ?", (creative_id,))

    def _import_selection(self) -> None:
        path = self.root / "_SELECCION_EXTRACCION.csv"
        for index, row in enumerate(read_csv_rows(path)):
            n = as_int(row.get("n"))
            ad_id = as_text(row.get("ad_archive_id"))
            creative_id = self._find_ad(ad_id=ad_id, archivo=as_text(row.get("archivo")))
            if creative_id is None:
                self._issue(
                    "error",
                    "selection_orphan",
                    "_SELECCION_EXTRACCION.csv",
                    index + 2,
                    ad_id,
                    "Selection row does not match an imported ad",
                    row,
                )
            if n is not None:
                self.selection_ad_ids[n] = creative_id
            payload_id = self._payload("_SELECCION_EXTRACCION.csv", index + 2, row, ad_id)
            score = as_float(row.get("score"))
            if creative_id is not None and score is not None:
                cursor = self.connection.execute(
                    """
                    INSERT OR IGNORE INTO legacy_score_snapshot
                        (ad_creative_id, score_type, score_value, source_file, source_row, details_json, created_at)
                    VALUES (?, 'legacy_selection_score', ?, '_SELECCION_EXTRACCION.csv', ?, ?, ?)
                    """,
                    (
                        creative_id,
                        score,
                        index + 2,
                        canonical_json({"n": n, "payload_id": payload_id, "replicas": row.get("replicas"), "dias": row.get("dias")}),
                        self.now,
                    ),
                )
                if cursor.rowcount:
                    self.counts["scores"] += 1

    def _import_elements(self) -> None:
        path = self.root / "_ELEMENTOS.csv"
        for index, row in enumerate(read_csv_rows(path)):
            n = as_int(row.get("n"))
            creative_id = self.selection_ad_ids.get(n) if n is not None else None
            self._payload("_ELEMENTOS.csv", index + 2, row, None)
            self.connection.execute(
                """
                INSERT OR IGNORE INTO legacy_element_observation
                    (selection_n, ad_creative_id, advertiser, product, payload_json,
                     source_file, source_row, created_at)
                VALUES (?, ?, ?, ?, ?, '_ELEMENTOS.csv', ?, ?)
                """,
                (
                    n,
                    creative_id,
                    as_text(row.get("anunciante")),
                    as_text(row.get("producto")),
                    canonical_json(row),
                    index + 2,
                    self.now,
                ),
            )

    def _import_copies(self) -> None:
        path = self.root / "_COPIES.csv"
        for index, row in enumerate(read_csv_rows(path)):
            ad_id = as_text(row.get("ad_archive_id"))
            creative_id = self._find_ad(ad_id=ad_id)
            payload_id = self._payload("_COPIES.csv", index + 2, row, ad_id)
            if creative_id is None:
                self._issue(
                    "warning",
                    "orphan_copy",
                    "_COPIES.csv",
                    index + 2,
                    ad_id,
                    "Copy row does not match an imported ad; preserved but not attached",
                    row,
                )
                continue
            self._insert_copy(
                creative_id=creative_id,
                primary_text=as_text(row.get("texto_principal")),
                headline=as_text(row.get("titulo")),
                description=as_text(row.get("descripcion")),
                cta=as_text(row.get("cta")),
                destination=as_text(row.get("destino")),
                extraction_method="legacy_copies",
                source_file="_COPIES.csv",
                source_row=index + 2,
                payload_id=payload_id,
                is_canonical=False,
            )

    def _import_ranking(self) -> None:
        path = self.root / "_RANKING_CUENTAS.csv"
        for index, row in enumerate(read_csv_rows(path)):
            page_id = as_text(row.get("page_id"))
            if page_id is None:
                self._issue(
                    "error",
                    "ranking_missing_page_id",
                    "_RANKING_CUENTAS.csv",
                    index + 2,
                    None,
                    "Ranking row has no page_id",
                    row,
                )
                continue
            name = as_text(row.get("anunciante"))
            advertiser_id = self._ensure_advertiser(page_id=page_id, name=name)
            self._add_alias(advertiser_id, name, "_RANKING_CUENTAS.csv", None, None)
            self._payload("_RANKING_CUENTAS.csv", index + 2, row, page_id)
            self.connection.execute(
                """
                UPDATE advertiser SET
                    reported_real_active_ads = ?,
                    reported_captured_creatives = ?,
                    reported_meta_cc_instances = ?,
                    reported_duplication_intensity = ?,
                    reported_catalog_pct = ?,
                    ranking_verdict = ?
                WHERE id = ?
                """,
                (
                    as_int(row.get("ads_activos_reales")),
                    as_int(row.get("creativos_capturados")),
                    as_int(row.get("instancias_meta_cc")),
                    as_float(row.get("intensidad_duplicacion")),
                    as_float(row.get("pct_catalogo")),
                    as_text(row.get("veredicto")),
                    advertiser_id,
                ),
            )

    def _import_reference_index(self) -> None:
        path = self.root / "_BANCO_CREATIVOS" / "_INDICE.csv"
        for index, row in enumerate(read_csv_rows(path)):
            origen = as_text(row.get("origen_img"))
            creative_id = self._find_ad(archivo=origen)
            if creative_id is None:
                self._issue(
                    "error",
                    "reference_orphan",
                    "_BANCO_CREATIVOS/_INDICE.csv",
                    index + 2,
                    None,
                    f"Reference image does not match an imported ad: {origen}",
                    row,
                )
            self._payload("_BANCO_CREATIVOS/_INDICE.csv", index + 2, row, None)
            external_key = as_text(row.get("ruta_banco")) or origen or f"row-{index + 2}"
            self.connection.execute(
                """
                INSERT OR IGNORE INTO reference_document
                    (kind, external_key, ad_creative_id, version, payload_json, content_hash,
                     status, source_file, source_row, created_at)
                VALUES ('banco_creativo', ?, ?, NULL, ?, ?, 'imported', ?, ?, ?)
                """,
                (
                    external_key,
                    creative_id,
                    canonical_json(row),
                    sha256_text(canonical_json(row)),
                    "_BANCO_CREATIVOS/_INDICE.csv",
                    index + 2,
                    self.now,
                ),
            )

    def _import_fichas(self) -> None:
        path = self.root / "_BLUEPRINTS" / "FICHAS" / "_MANIFIESTO.csv"
        for index, row in enumerate(read_csv_rows(path)):
            ruta = as_text(row.get("ruta_json"))
            ficha_id = as_text(row.get("ficha_id")) or f"row-{index + 2}"
            if not ruta:
                self._issue("error", "ficha_missing_path", "_BLUEPRINTS/FICHAS/_MANIFIESTO.csv", index + 2, ficha_id, "Ficha row has no ruta_json", row)
                continue
            ficha_path = self.root / "_BLUEPRINTS" / Path(ruta.replace("\\", "/"))
            if not ficha_path.exists():
                self._issue("error", "ficha_missing_file", "_BLUEPRINTS/FICHAS/_MANIFIESTO.csv", index + 2, ficha_id, f"Ficha JSON missing: {ruta}", row)
                continue
            payload = read_json(ficha_path)
            ad_id = as_text(row.get("ad_archive_id")) or as_text((payload.get("origen") or {}).get("ad_archive_id"))
            creative_id = self._find_ad(ad_id=ad_id, archivo=as_text(row.get("archivo")))
            self._payload("_BLUEPRINTS/FICHAS/_MANIFIESTO.csv", index + 2, row, ad_id)
            self.connection.execute(
                """
                INSERT OR IGNORE INTO reference_document
                    (kind, external_key, ad_creative_id, version, payload_json, content_hash,
                     status, source_file, source_row, created_at)
                VALUES ('ficha', ?, ?, ?, ?, ?, 'imported', ?, ?, ?)
                """,
                (
                    ficha_id,
                    creative_id,
                    as_text(payload.get("schema_version")),
                    canonical_json(payload),
                    sha256_text(canonical_json(payload)),
                    normalize_relpath(self.root, ficha_path),
                    index + 2,
                    self.now,
                ),
            )

    def _import_canonical(self) -> None:
        for path in sorted((self.root / "_BLUEPRINTS" / "CANONICOS").glob("*.json")):
            payload = read_json(path)
            key = as_text(payload.get("canonico_id")) or path.stem
            self.connection.execute(
                """
                INSERT OR IGNORE INTO reference_document
                    (kind, external_key, ad_creative_id, version, payload_json, content_hash,
                     status, source_file, source_row, created_at)
                VALUES ('canonico', ?, NULL, ?, ?, ?, 'imported', ?, 1, ?)
                """,
                (
                    key,
                    as_text(payload.get("schema_version")),
                    canonical_json(payload),
                    sha256_text(canonical_json(payload)),
                    normalize_relpath(self.root, path),
                    self.now,
                ),
            )

    def _import_blueprints(self) -> None:
        for kind, pattern in (
            ("blueprint", "blueprint_*.json"),
            ("blueprint_filled_t01", "LLENO_T01_*.json"),
        ):
            for path in sorted((self.root / "_BLUEPRINTS").glob(pattern)):
                payload = read_json(path)
                key = as_text(payload.get("id")) or path.stem
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO reference_document
                        (kind, external_key, ad_creative_id, version, payload_json, content_hash,
                         status, source_file, source_row, created_at)
                    VALUES (?, ?, NULL, ?, ?, ?, 'imported', ?, 1, ?)
                    """,
                    (
                        kind,
                        key,
                        as_text(payload.get("version")),
                        canonical_json(payload),
                        sha256_text(canonical_json(payload)),
                        normalize_relpath(self.root, path),
                        self.now,
                    ),
                )

    def _fact(
        self,
        product_id: int,
        fact_key: str,
        value: Any,
        unit: str | None = None,
        currency: str | None = None,
        evidence_ref: str | None = None,
    ) -> None:
        if value is None:
            return
        self.connection.execute(
            """
            INSERT OR IGNORE INTO product_fact
                (product_id, fact_key, value, unit, currency, evidence_ref,
                 verification_status, valid_from, valid_to, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'operator_provided', NULL, NULL, ?)
            """,
            (product_id, fact_key, str(value), unit, currency, evidence_ref, self.now),
        )

    def _import_product(self) -> None:
        path = self.root / "_BLUEPRINTS" / "ficha_tinnidrop.json"
        payload = read_json(path)
        source_file = normalize_relpath(self.root, path)
        product_name = as_text(payload.get("producto")) or "Tinnidrop"
        brand = as_text(payload.get("marca"))
        market = (payload.get("mercado") or {}).get("pais")
        category = (payload.get("producto_data") or {}).get("categoria")
        sku = as_text(payload.get("slug"))
        self.connection.execute(
            """
            INSERT OR IGNORE INTO product
                (name, brand, market, category, sku, status, source_file, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (product_name, brand, market, category, sku, source_file, canonical_json(payload), self.now, self.now),
        )
        row = self.connection.execute(
            "SELECT id FROM product WHERE name = ? AND COALESCE(brand, '') = COALESCE(?, '')",
            (product_name, brand),
        ).fetchone()
        if row is None:
            raise RuntimeError("Could not create product")
        product_id = int(row["id"])
        currency = as_text((payload.get("mercado") or {}).get("moneda"))
        self._fact(product_id, "market_country", (payload.get("mercado") or {}).get("pais"), evidence_ref=source_file)
        self._fact(product_id, "market_currency", currency, currency=currency, evidence_ref=source_file)
        self._fact(product_id, "sales_channel", (payload.get("mercado") or {}).get("canal_cierre"), evidence_ref=source_file)
        self._fact(product_id, "supplier_cost", payload.get("costo_proveedor_q"), currency=currency, evidence_ref=source_file)
        offer = payload.get("oferta") or {}
        self._fact(product_id, "offer_guarantee_days", offer.get("dias_garantia"), unit="days", evidence_ref=source_file)
        for tier in offer.get("tiers") or []:
            quantity = tier.get("cantidad")
            if quantity is None:
                continue
            self._fact(product_id, f"offer_tier_{quantity}_price", tier.get("precio"), currency=currency, evidence_ref=source_file)
            self._fact(product_id, f"offer_tier_{quantity}_units", quantity, unit=tier.get("unidad"), evidence_ref=source_file)
        product_data = payload.get("producto_data") or {}
        self._fact(product_id, "ingredient_star", product_data.get("ingrediente_estrella"), evidence_ref=source_file)
        self._fact(product_id, "dose", product_data.get("dosis"), evidence_ref=source_file)
        self._fact(product_id, "presentation", product_data.get("presentacion"), evidence_ref=source_file)
        audience = payload.get("audiencia") or {}
        self._fact(product_id, "audience_age", audience.get("edad"), evidence_ref=source_file)
        self._fact(product_id, "audience_gender", audience.get("genero"), evidence_ref=source_file)
        self._fact(product_id, "awareness_level", audience.get("nivel_consciencia"), evidence_ref=source_file)

        claims = list(product_data.get("claims_en_empaque") or [])
        if "Registro MSPAS" not in claims:
            claims.append("Registro MSPAS")
        for claim_text in claims:
            claim_type = "regulatory" if claim_text == "Registro MSPAS" else "packaging_label"
            self.connection.execute(
                """
                INSERT OR IGNORE INTO claim
                    (product_id, claim_text, claim_type, evidence_refs, status, markets,
                     approved_by, reviewed_at, source_file, created_at)
                VALUES (?, ?, ?, ?, 'evidence_needed', 'GT', NULL, NULL, ?, ?)
                """,
                (
                    product_id,
                    claim_text,
                    claim_type,
                    canonical_json([source_file, "operator-provided; not independently verified"]),
                    source_file,
                    self.now,
                ),
            )

    def _import_summary_issues(self) -> None:
        leeme = self.root / "_BANCO_CREATIVOS" / "_LEEME.md"
        if leeme.exists():
            self._issue(
                "info",
                "documentation_stale",
                "_BANCO_CREATIVOS/_LEEME.md",
                None,
                None,
                "Legacy README reports 43 references and missing C9; current index has 48 and C9 has 5. Preserved as documentation issue.",
                {"actual_reference_rows": 48},
            )

    def _finish_job(self, counts: dict[str, int]) -> None:
        evidence_hash = sha256_text(canonical_json(counts))
        cursor = self.connection.execute(
            """
            INSERT INTO job_run (job_type, status, started_at, finished_at, counts_json, errors_json)
            VALUES ('legacy_import', 'completed', ?, ?, ?, NULL)
            """,
            (self.now, utc_now(), canonical_json(counts)),
        )
        self.connection.execute(
            """
            INSERT INTO audit_event
                (actor, event_type, object_type, object_id, timestamp, before_hash, after_hash, reason)
            VALUES ('ads_intel', 'legacy_import_completed', 'database', ?, ?, NULL, ?, ?)
            """,
            (str(cursor.lastrowid), utc_now(), evidence_hash, "Phase 1 canonical import"),
        )


def import_all(root: Path, db_path: Path) -> dict[str, int]:
    connection = connect(db_path)
    try:
        apply_migrations(connection)
        with connection:
            importer = LegacyImporter(connection, root)
            return importer.run()
    finally:
        connection.close()

