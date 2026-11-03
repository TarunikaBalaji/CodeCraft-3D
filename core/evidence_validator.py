"""Deterministic provenance checks for AI-extracted regulation constraints.

This validates traceability and basic textual support only. It does NOT
establish legal applicability, interpret exceptions, or certify compliance.
"""
from __future__ import annotations

import re
from typing import Any

UNIT_GROUPS = {
    "length_m": {"m", "meter", "meters", "metre", "metres"},
    "length_ft": {"ft", "feet", "foot"},
    "percent": {"%", "percent", "percentage"},
}
SUPPORTED_UNITS = set().union(*UNIT_GROUPS.values())


def _unit_group(unit: str) -> str | None:
    value = unit.strip().casefold()
    return next((name for name, aliases in UNIT_GROUPS.items() if value in aliases), None)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def validate_candidate(candidate: dict[str, Any], pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a candidate annotated with deterministic evidence checks."""
    issues: list[str] = []
    page_number = candidate.get("page_number")
    excerpt = candidate.get("source_excerpt")
    value = candidate.get("value")
    unit = candidate.get("unit")

    page = next((p for p in pages if p.get("page_number") == page_number), None)
    if page is None:
        issues.append("CITED_PAGE_NOT_FOUND")
    elif not isinstance(excerpt, str) or not excerpt.strip():
        issues.append("SOURCE_EXCERPT_MISSING")
    elif _normalise(excerpt) not in _normalise(page.get("text", "")):
        issues.append("SOURCE_EXCERPT_NOT_FOUND_ON_CITED_PAGE")

    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        issues.append("INVALID_OR_MISSING_NUMERIC_VALUE")
    if not isinstance(unit, str) or unit.strip().casefold() not in SUPPORTED_UNITS:
        issues.append("UNSUPPORTED_OR_MISSING_UNIT")

    if page is not None and isinstance(excerpt, str) and excerpt.strip() and value is not None and isinstance(unit, str):
        excerpt_text = _normalise(excerpt)
        # The value and unit must both occur in the cited excerpt; this is a
        # conservative lexical gate, not semantic interpretation.
        number = str(value).rstrip("0").rstrip(".") if isinstance(value, float) else str(value)
        number_present = re.search(rf"(?<!\d){re.escape(number)}(?!\d)", excerpt_text) is not None
        unit_group = _unit_group(unit)
        unit_present = unit_group is not None and any(
            alias in excerpt_text for alias in UNIT_GROUPS[unit_group]
        )
        if not number_present:
            issues.append("NUMERIC_VALUE_NOT_PRESENT_IN_EXCERPT")
        if not unit_present:
            issues.append("UNIT_NOT_PRESENT_IN_EXCERPT")

    result = dict(candidate)
    result["evidence_check"] = {
        "passed": not issues,
        "issues": issues,
        "method": "exact_page_excerpt_and_numeric_unit_presence",
        "legal_interpretation_verified": False,
    }
    result["status"] = "needs_human_review" if issues else "extracted"
    return result
