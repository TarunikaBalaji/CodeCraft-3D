
import pytest

from core.geometry import Site, Setbacks, Building
from core.schemas import (
    ConstraintType,
    RegulationConstraint,
    VerificationStatus,
)
from core.regulation_graph import LivingRegulationGraph
from core.dependency_engine import DependencyEngine


def make_constraint(
    constraint_id,
    constraint_type,
    value,
    unit,
    status=VerificationStatus.VERIFIED,
):
    return RegulationConstraint(
        constraint_id=constraint_id,
        constraint_type=constraint_type,
        value=value,
        unit=unit,
        document_id="TN-REG-001",
        page_number=12,
        clause_reference="4.2",
        source_excerpt=f"Test regulation: {constraint_type.value}",
        status=status,
    )


def make_engine():
    graph = LivingRegulationGraph()

    height_constraint = make_constraint(
        "HEIGHT-001",
        ConstraintType.MAX_HEIGHT,
        40,
        "feet",
    )

    graph.add_constraint(height_constraint)

    return DependencyEngine(graph), graph


def test_verified_constraint_is_collected():
    engine, _ = make_engine()

    verified = engine.get_verified_constraints()

    assert "max_height" in verified
    assert verified["max_height"]["value"] == 40


def test_unverified_constraint_is_not_collected():
    graph = LivingRegulationGraph()

    constraint = make_constraint(
        "HEIGHT-002",
        ConstraintType.MAX_HEIGHT,
        40,
        "feet",
        VerificationStatus.NEEDS_HUMAN_REVIEW,
    )

    graph.add_constraint(constraint)

    engine = DependencyEngine(graph)

    verified = engine.get_verified_constraints()

    assert "max_height" not in verified


def test_unverified_constraint_cannot_trigger_recalculation():
    graph = LivingRegulationGraph()

    constraint = make_constraint(
        "HEIGHT-003",
        ConstraintType.MAX_HEIGHT,
        40,
        "feet",
        VerificationStatus.NEEDS_HUMAN_REVIEW,
    )

    graph.add_constraint(constraint)

    engine = DependencyEngine(graph)

    with pytest.raises(ValueError):
        engine.get_constraint_impact("HEIGHT-003")


def test_verified_height_constraint_triggers_recalculation():
    engine, _ = make_engine()

    impact = engine.get_constraint_impact("HEIGHT-001")

    assert impact["status"] == "verified"
    assert impact["requires_recalculation"] is True
    assert impact["affected_geometry"] == [
        "geometry:height_validation"
    ]


def test_recalculation_applies_verified_height():
    engine, _ = make_engine()

    result = engine.recalculate(
        changed_constraint_id="HEIGHT-001",
        site=Site(width=40, depth=60),
        setbacks=Setbacks(
            front=10,
            rear=5,
            left=5,
            right=5,
        ),
        building=Building(
            width=30,
            depth=35,
            height=42,
            x=5,
            y=10,
        ),
        max_height=50,
        max_coverage_percent=50,
    )

    assert result["recalculation_status"] == "completed"
    assert result["applied_constraints"]["max_height"]["value"] == 40
    assert result["geometry_result"].violations == [
        "HEIGHT_VIOLATION"
    ]


def test_unknown_constraint_raises_error():
    engine, _ = make_engine()

    with pytest.raises(ValueError):
        engine.get_constraint_impact("UNKNOWN-999")
