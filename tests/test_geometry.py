
from core.geometry import (
    Site,
    Setbacks,
    Building,
    calculate_geometry,
)


def test_valid_footprint_with_height_violation():
    site = Site(width=40, depth=60)

    setbacks = Setbacks(
        front=10,
        rear=5,
        left=5,
        right=5,
    )

    building = Building(
        width=30,
        depth=35,
        height=50,
        x=5,
        y=10,
    )

    result = calculate_geometry(
        site=site,
        setbacks=setbacks,
        building=building,
        max_height=45,
        max_coverage_percent=50,
    )

    assert result.site_area == 2400
    assert result.buildable_width == 30
    assert result.buildable_depth == 45
    assert result.buildable_area == 1350
    assert result.max_coverage_area == 1200
    assert result.building_footprint == 1050
    assert result.actual_coverage_percent == 43.75

    assert result.violations == ["HEIGHT_VIOLATION"]


def test_multiple_simultaneous_violations():
    site = Site(width=40, depth=60)

    setbacks = Setbacks(
        front=10,
        rear=5,
        left=5,
        right=5,
    )

    building = Building(
        width=35,
        depth=40,
        height=50,
        x=2,
        y=5,
    )

    result = calculate_geometry(
        site=site,
        setbacks=setbacks,
        building=building,
        max_height=45,
        max_coverage_percent=40,
    )

    assert "SETBACK_VIOLATION" in result.violations
    assert "HEIGHT_VIOLATION" in result.violations
    assert "COVERAGE_VIOLATION" in result.violations
