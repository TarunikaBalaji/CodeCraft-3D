
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Site:
    width: float
    depth: float


@dataclass
class Setbacks:
    front: float
    rear: float
    left: float
    right: float


@dataclass
class Building:
    width: float
    depth: float
    height: float
    x: float = 0.0
    y: float = 0.0


@dataclass
class GeometryResult:
    site_area: float
    buildable_width: float
    buildable_depth: float
    buildable_area: float
    max_coverage_area: float
    building_footprint: float
    actual_coverage_percent: float
    maximum_height: float
    proposed_height: float
    violations: list[str]
    measurements: dict[str, Any]

    def to_dict(self):
        return asdict(self)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0


def validate_positive(name: str, value: float):
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")


def calculate_geometry(
    site: Site,
    setbacks: Setbacks,
    building: Building,
    max_height: float,
    max_coverage_percent: float,
) -> GeometryResult:

    # 1. Validate input dimensions
    validate_positive("Site width", site.width)
    validate_positive("Site depth", site.depth)
    validate_positive("Building width", building.width)
    validate_positive("Building depth", building.depth)
    validate_positive("Building height", building.height)
    validate_positive("Maximum height", max_height)

    setback_values = {
        "Front setback": setbacks.front,
        "Rear setback": setbacks.rear,
        "Left setback": setbacks.left,
        "Right setback": setbacks.right,
    }

    for name, value in setback_values.items():
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

    if not 0 <= max_coverage_percent <= 100:
        raise ValueError("Maximum coverage must be between 0 and 100.")

    # 2. Calculate the buildable envelope
    buildable_width = (
        site.width - setbacks.left - setbacks.right
    )

    buildable_depth = (
        site.depth - setbacks.front - setbacks.rear
    )

    if buildable_width <= 0 or buildable_depth <= 0:
        raise ValueError(
            "Setbacks leave no positive buildable envelope."
        )

    site_area = site.width * site.depth
    buildable_area = buildable_width * buildable_depth

    # 3. Calculate permitted coverage
    max_coverage_area = (
        site_area * max_coverage_percent / 100
    )

    # 4. Calculate proposed building footprint
    building_footprint = building.width * building.depth

    actual_coverage_percent = (
        building_footprint / site_area
    ) * 100

    # 5. Calculate building boundaries
    building_left = building.x
    building_right = building.x + building.width

    building_front = building.y
    building_rear = building.y + building.depth

    # 6. Calculate permitted boundaries
    permitted_left = setbacks.left
    permitted_right = site.width - setbacks.right

    permitted_front = setbacks.front
    permitted_rear = site.depth - setbacks.rear

    # 7. Check every violation independently
    violations = []

    # Plot boundary checks
    if (
        building_left < 0
        or building_right > site.width
        or building_front < 0
        or building_rear > site.depth
    ):
        violations.append("SITE_BOUNDARY_VIOLATION")

    # Setback checks
    if (
        building_left < permitted_left
        or building_right > permitted_right
        or building_front < permitted_front
        or building_rear > permitted_rear
    ):
        violations.append("SETBACK_VIOLATION")

    # Height checks
    if building.height > max_height:
        violations.append("HEIGHT_VIOLATION")

    # Coverage checks
    if building_footprint > max_coverage_area:
        violations.append("COVERAGE_VIOLATION")

    # 8. Prepare detailed measurements
    measurements = {
        "building_left": building_left,
        "building_right": building_right,
        "building_front": building_front,
        "building_rear": building_rear,
        "permitted_left": permitted_left,
        "permitted_right": permitted_right,
        "permitted_front": permitted_front,
        "permitted_rear": permitted_rear,
        "height_excess": max(0, building.height - max_height),
        "coverage_excess_area": max(
            0, building_footprint - max_coverage_area
        ),
        "width_outside_envelope": max(
            0, building.width - buildable_width
        ),
        "depth_outside_envelope": max(
            0, building.depth - buildable_depth
        ),
    }

    return GeometryResult(
        site_area=site_area,
        buildable_width=buildable_width,
        buildable_depth=buildable_depth,
        buildable_area=buildable_area,
        max_coverage_area=max_coverage_area,
        building_footprint=building_footprint,
        actual_coverage_percent=actual_coverage_percent,
        maximum_height=max_height,
        proposed_height=building.height,
        violations=violations,
        measurements=measurements,
    )
