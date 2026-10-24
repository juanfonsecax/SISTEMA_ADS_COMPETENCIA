from __future__ import annotations

import sqlite3
from typing import Any

from .classification import _event, _insert_assignment, finish_run, start_run
from .taxonomy import TAXONOMY_VERSION, validate_tag
from .util import canonical_json, sha256_text

ENRICHMENT_CONTRACT_VERSION = "creative-enrichment-v1"


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _normalize_confidence(value: Any, basis: Any) -> tuple[float | None, str]:
    if value is None:
        return None, _require_text(basis, "confidence_basis") if basis else "model_output_without_numeric_confidence"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("confidence must be a number between 0 and 1, or null")
    number = float(value)
    if not 0 <= number <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return number, _require_text(basis, "confidence_basis")


def validate_enrichment_payload(
    connection: sqlite3.Connection,
    payload: Any,
    *,
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[str, Any]:
    data = _require_mapping(payload, "payload")
    if data.get("contract_version") != ENRICHMENT_CONTRACT_VERSION:
        raise ValueError(f"contract_version must be {ENRICHMENT_CONTRACT_VERSION!r}")
    if data.get("taxonomy_version") != taxonomy_version:
        raise ValueError(f"taxonomy_version must be {taxonomy_version!r}")
    creative_id = data.get("ad_creative_id")
    if not isinstance(creative_id, int):
        raise ValueError("ad_creative_id must be an integer")
    if connection.execute("SELECT 1 FROM ad_creative WHERE id = ?", (creative_id,)).fetchone() is None:
        raise ValueError(f"Unknown ad_creative_id: {creative_id}")
    asset_id = data.get("asset_id")
    if asset_id is not None:
        if not isinstance(asset_id, int):
            raise ValueError("asset_id must be an integer or null")
        if connection.execute("SELECT 1 FROM asset WHERE id = ?", (asset_id,)).fetchone() is None:
            raise ValueError(f"Unknown asset_id: {asset_id}")
    model = _require_mapping(data.get("model"), "model")
    provider = _require_text(model.get("provider"), "model.provider")
    model_version = _require_text(model.get("model_version"), "model.model_version")
    prompt_version = model.get("prompt_version")
    if prompt_version is not None:
        prompt_version = _require_text(prompt_version, "model.prompt_version")
    raw_outputs = data.get("outputs")
    if not isinstance(raw_outputs, list):
        raise ValueError("outputs must be a list")
    outputs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_outputs):
        item = _require_mapping(raw, f"outputs[{index}]")
        dimension = _require_text(item.get("dimension"), f"outputs[{index}].dimension")
        tag_key = _require_text(item.get("tag_key"), f"outputs[{index}].tag_key")
        key = (dimension, tag_key)
        if key in seen:
            raise ValueError(f"Duplicate output tag: {dimension}:{tag_key}")
        seen.add(key)
        target_tag_id = validate_tag(connection, dimension, tag_key, version=taxonomy_version)
        confidence, confidence_basis = _normalize_confidence(
            item.get("confidence"), item.get("confidence_basis")
        )
        evidence = item.get("evidence")
        if evidence is not None and not isinstance(evidence, (dict, list, str)):
            raise ValueError(f"outputs[{index}].evidence must be an object, list, or string")
        rationale = item.get("rationale")
        if rationale is not None and not isinstance(rationale, str):
            raise ValueError(f"outputs[{index}].rationale must be a string")
        outputs.append(
            {
                "dimension": dimension,
                "tag_key": tag_key,
                "tag_definition_id": target_tag_id,
                "confidence": confidence,
                "confidence_basis": confidence_basis,
                "evidence": evidence,
                "rationale": rationale,
            }
        )
    raw_unknowns = data.get("unknowns", [])
    if not isinstance(raw_unknowns, list):
        raise ValueError("unknowns must be a list")
    unknowns: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_unknowns):
        item = _require_mapping(raw, f"unknowns[{index}]")
        dimension = _require_text(item.get("dimension"), f"unknowns[{index}].dimension")
        if connection.execute(
            """
            SELECT 1 FROM taxonomy_dimension
            WHERE taxonomy_version = ? AND dimension = ?
            """,
            (taxonomy_version, dimension),
        ).fetchone() is None:
            raise ValueError(f"Unknown taxonomy dimension in unknowns: {dimension}")
        reason = _require_text(item.get("reason"), f"unknowns[{index}].reason")
        unknowns.append({"dimension": dimension, "reason": reason})
    raw_claims = data.get("claims", [])
    if not isinstance(raw_claims, list):
        raise ValueError("claims must be a list")
    claims: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_claims):
        item = _require_mapping(raw, f"claims[{index}]")
        if item.get("approved") is True or item.get("status") == "approved":
            raise ValueError("Enrichment output cannot approve a claim")
        text = _require_text(item.get("text"), f"claims[{index}].text")
        claims.append(
            {
                "text": text,
                "claim_type": item.get("claim_type"),
                "risk": item.get("risk"),
                "requires_human_review": True,
            }
        )
    cost = data.get("cost")
    if cost is not None:
        cost = _require_mapping(cost, "cost")
        currency = _require_text(cost.get("currency"), "cost.currency").upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("cost.currency must be a three-letter code")
        amount = cost.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise ValueError("cost.amount must be a non-negative number")
        cost = {"currency": currency, "amount": float(amount), "unit": cost.get("unit")}
    return {
        "contract_version": ENRICHMENT_CONTRACT_VERSION,
        "taxonomy_version": taxonomy_version,
        "ad_creative_id": creative_id,
        "asset_id": asset_id,
        "model": {
            "provider": provider,
            "model_version": model_version,
            "prompt_version": prompt_version,
        },
        "outputs": outputs,
        "unknowns": unknowns,
        "claims": claims,
        "cost": cost,
        "source_file": data.get("source_file"),
        "notes": data.get("notes"),
    }


def ingest_enrichment(
    connection: sqlite3.Connection,
    payload: Any,
    *,
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[str, Any]:
    normalized = validate_enrichment_payload(
        connection, payload, taxonomy_version=taxonomy_version
    )
    model = normalized["model"]
    assigned_by = f"{model['provider']}:{model['model_version']}"
    run_id = start_run(
        connection,
        run_type="enrichment",
        method="enrichment_contract_v1",
        taxonomy_version=taxonomy_version,
        model_version=model["model_version"],
        prompt_version=model["prompt_version"],
        contract_version=ENRICHMENT_CONTRACT_VERSION,
        notes=normalized["notes"],
    )
    counts = {
        "outputs": len(normalized["outputs"]),
        "assignments_inserted": 0,
        "assignments_skipped_protected": 0,
        "assignments_skipped_existing": 0,
        "unknowns": len(normalized["unknowns"]),
        "claims_pending_human_review": len(normalized["claims"]),
    }
    errors: list[dict[str, Any]] = []
    try:
        for output in normalized["outputs"]:
            protected = connection.execute(
                """
                SELECT 1
                FROM ad_tag
                WHERE ad_creative_id = ? AND tag_definition_id = ?
                  AND review_status IN ('approved', 'reviewed')
                LIMIT 1
                """,
                (normalized["ad_creative_id"], output["tag_definition_id"]),
            ).fetchone()
            if protected is not None:
                counts["assignments_skipped_protected"] += 1
                continue
            existing = connection.execute(
                """
                SELECT id
                FROM ad_tag
                WHERE ad_creative_id = ? AND tag_definition_id = ?
                  AND method = 'enrichment_contract_v1' AND assigned_by = ?
                LIMIT 1
                """,
                (normalized["ad_creative_id"], output["tag_definition_id"], assigned_by),
            ).fetchone()
            if existing is not None:
                counts["assignments_skipped_existing"] += 1
                continue
            evidence = {
                "contract_version": ENRICHMENT_CONTRACT_VERSION,
                "model": model,
                "evidence": output["evidence"],
                "rationale": output["rationale"],
                "unknowns": normalized["unknowns"],
                "claims_pending_human_review": normalized["claims"],
                "run_id": run_id,
            }
            tag_id = _insert_assignment(
                connection,
                creative_id=normalized["ad_creative_id"],
                asset_id=normalized["asset_id"],
                target_tag_id=output["tag_definition_id"],
                confidence=output["confidence"],
                confidence_label=None,
                confidence_basis=output["confidence_basis"],
                assigned_by=assigned_by,
                method="enrichment_contract_v1",
                review_status="suggested",
                evidence=evidence,
                source_file=normalized["source_file"],
                source_row=None,
                taxonomy_version=taxonomy_version,
                run_id=run_id,
                model_version=model["model_version"],
                prompt_version=model["prompt_version"],
            )
            if tag_id is None:
                counts["assignments_skipped_existing"] += 1
                continue
            _event(
                connection,
                tag_id,
                "created_from_enrichment",
                None,
                "suggested",
                assigned_by,
                output["rationale"],
                evidence,
            )
            counts["assignments_inserted"] += 1
        finish_run(
            connection,
            run_id,
            status="completed_with_errors" if errors else "completed",
            counts=counts,
            errors=errors,
            cost=normalized["cost"],
        )
    except Exception as exc:
        finish_run(
            connection,
            run_id,
            status="failed",
            counts=counts,
            errors=errors + [{"error": str(exc)}],
            cost=normalized["cost"],
        )
        raise
    return {
        "run_id": run_id,
        "contract_version": ENRICHMENT_CONTRACT_VERSION,
        "taxonomy_version": taxonomy_version,
        "ad_creative_id": normalized["ad_creative_id"],
        "cost": normalized["cost"],
        **counts,
        "errors": errors,
    }


def list_enrichment_runs(connection, *, limit: int = 20) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, taxonomy_version, run_type, method, model_version, prompt_version,
                   contract_version, started_at, finished_at, status, counts_json,
                   errors_json, cost_json, notes
            FROM classification_run
            WHERE run_type = 'enrichment'
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        )
    ]


def enrichment_contract_schema() -> dict[str, Any]:
    schema = {
        "contract_version": ENRICHMENT_CONTRACT_VERSION,
        "required": ["contract_version", "taxonomy_version", "ad_creative_id", "model", "outputs"],
        "optional": ["asset_id", "unknowns", "claims", "cost", "source_file", "notes"],
        "model": {"provider": "string", "model_version": "string", "prompt_version": "string|null"},
        "outputs": [
            {
                "dimension": "canonical dimension key",
                "tag_key": "canonical tag key",
                "confidence": "number 0..1 or null",
                "confidence_basis": "string; required when confidence is not null",
                "evidence": "object, list, or string",
                "rationale": "string",
            }
        ],
        "unknowns": [{"dimension": "canonical dimension key", "reason": "string"}],
        "claims": [{"text": "string", "claim_type": "string|null", "risk": "string|null"}],
        "cost": {"currency": "ISO 4217", "amount": "non-negative number", "unit": "string|null"},
        "constraints": {
            "no_claim_approval": True,
            "no_paid_provider_call": True,
            "no_overwrite_of_approved_tags": True,
            "unknown_tags_rejected": True,
        },
    }
    schema["schema_hash"] = sha256_text(canonical_json(schema))
    return schema
