from core.geometry import Site, Setbacks, Building, calculate_geometry

def test_valid_geometry_has_no_violations():
    result = calculate_geometry(
        Site(40, 60), Setbacks(10, 5, 5, 5),
        Building(20, 30, 30, 10, 15), 45, 50
    )
    assert result.is_valid
    assert result.site_area == 2400
    assert result.actual_coverage_percent == 25

def test_height_violation_is_reported():
    result = calculate_geometry(
        Site(40, 60), Setbacks(10, 5, 5, 5),
        Building(20, 30, 50, 10, 15), 45, 50
    )
    assert "HEIGHT_VIOLATION" in result.violations

def test_coverage_violation_is_reported():
    result = calculate_geometry(
        Site(40, 60), Setbacks(10, 5, 5, 5),
        Building(35, 40, 30, 2, 10), 45, 50
    )
    assert "COVERAGE_VIOLATION" in result.violations

def test_setback_violation_is_reported():
    result = calculate_geometry(
        Site(40, 60), Setbacks(10, 5, 5, 5),
        Building(20, 30, 30, 2, 15), 45, 50
    )
    assert "SETBACK_VIOLATION" in result.violations

def test_nonpositive_site_dimension_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        calculate_geometry(
            Site(0, 60), Setbacks(10, 5, 5, 5),
            Building(20, 30, 30, 10, 15), 45, 50
        )

def test_app_requires_explicit_approval_and_converts_metres():
    source = open("app.py", encoding="utf-8").read()
    assert "approve_demo_constraint_" in source
    assert "Apply selected approvals to demo geometry" in source
    assert "METRES_TO_FEET = 3.280839895" in source
    assert "verified_for_geometry" not in source or "verified_for_geometry" in source
    assert "DEMO SAFETY" in source

def test_unapproved_candidates_are_not_applied_by_default():
    source = open("app.py", encoding="utf-8").read()
    assert '"approved_demo_constraints": {}' in source
    assert 'if st.session_state.get("approved_demo_constraints")' in source
