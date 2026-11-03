"""PDF -> Muse Spark candidates -> deterministic evidence checks."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.document_processor import process_pdf
from core.evidence_validator import validate_candidate
from core.meta_client import extract_constraints_with_muse_spark

ALLOWED_TYPES = {
    "front_setback", "rear_setback", "left_setback", "right_setback",
    "max_height", "max_site_coverage",
}


def run_regulation_pipeline(pdf_path: str | Path, api_key: str | None = None,
                            model: str = "muse-spark-1.3") -> dict[str, Any]:
    document = process_pdf(pdf_path)
    if document["processing_status"] != "SUCCESS":
        raise ValueError("PDF text extraction failed. This document needs OCR or a text-based PDF.")

    ai_result = extract_constraints_with_muse_spark(
        pages=document["pages"], document_id=document["document_id"],
        api_key=api_key, model=model,
    )
    checked: list[dict[str, Any]] = []
    for index, raw in enumerate(ai_result.get("constraints", []), start=1):
        if not isinstance(raw, dict):
            continue
        candidate = dict(raw)
        candidate.setdefault("constraint_id", f"{document['document_id']}-candidate-{index}")
        candidate["document_id"] = document["document_id"]
        if candidate.get("constraint_type") not in ALLOWED_TYPES:
            candidate["evidence_check"] = {
                "passed": False, "issues": ["UNSUPPORTED_CONSTRAINT_TYPE"],
                "method": "schema_allowlist", "legal_interpretation_verified": False,
            }
            candidate["status"] = "needs_human_review"
        else:
            candidate = validate_candidate(candidate, document["pages"])
        checked.append(candidate)

    return {
        "document": {
            "document_id": document["document_id"],
            "file_name": document["file_name"],
            "page_count": document["page_count"],
            "processing_status": document["processing_status"],
        },
        "provider": ai_result.get("provider", "Meta Model API"),
        "model": ai_result.get("model", model),
        "constraints": checked,
        "ambiguities": ai_result.get("ambiguities", []),
        "verified_for_geometry": [],
        "disclaimer": (
            "Evidence checks establish source traceability only. They do not establish "
            "legal applicability or certify regulatory compliance. Human review is required."
        ),
    }
