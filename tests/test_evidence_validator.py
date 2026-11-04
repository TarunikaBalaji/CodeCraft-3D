from core.evidence_validator import validate_candidate


def page(text):
    return [{"page_number": 4, "text": text}]


def candidate(**overrides):
    data = {
        "constraint_id": "c1", "constraint_type": "front_setback",
        "value": 3.0, "unit": "m", "page_number": 4,
        "source_excerpt": "The minimum front setback shall be 3 metres.",
    }
    data.update(overrides)
    return data


def test_valid_excerpt_passes_traceability_check():
    result = validate_candidate(candidate(), page("The minimum front setback shall be 3 metres."))
    assert result["evidence_check"]["passed"] is True
    assert result["status"] == "extracted"
    assert result["evidence_check"]["legal_interpretation_verified"] is False


def test_wrong_page_is_flagged():
    result = validate_candidate(candidate(page_number=9), page("The minimum front setback shall be 3 metres."))
    assert "CITED_PAGE_NOT_FOUND" in result["evidence_check"]["issues"]


def test_excerpt_not_on_cited_page_is_flagged():
    result = validate_candidate(candidate(), page("Front setback is 2 metres."))
    assert "SOURCE_EXCERPT_NOT_FOUND_ON_CITED_PAGE" in result["evidence_check"]["issues"]


def test_number_not_in_excerpt_is_flagged():
    result = validate_candidate(candidate(value=5.0), page("The minimum front setback shall be 3 metres."))
    assert "NUMERIC_VALUE_NOT_PRESENT_IN_EXCERPT" in result["evidence_check"]["issues"]


def test_unit_mismatch_is_flagged():
    result = validate_candidate(candidate(unit="ft"), page("The minimum front setback shall be 3 metres."))
    assert "UNIT_NOT_PRESENT_IN_EXCERPT" in result["evidence_check"]["issues"]


def test_missing_excerpt_is_flagged():
    result = validate_candidate(candidate(source_excerpt=""), page("Some text"))
    assert "SOURCE_EXCERPT_MISSING" in result["evidence_check"]["issues"]
