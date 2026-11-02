
import pytest

from core.schemas import (
    ConstraintType,
    RegulationConstraint,
    VerificationStatus,
)
from core.regulation_graph import LivingRegulationGraph
from core.change_impact import ChangeImpactEngine


def make_engine(status=VerificationStatus.VERIFIED):
    graph = LivingRegulationGraph()

    constraint = RegulationConstraint(
        constraint_id="HEIGHT-001",
        constraint_type=ConstraintType.MAX_HEIGHT,
        value=40,
        unit="feet",
        document_id="TN-REG-001",
        page_number=12,
        clause_reference="4.2",
        source_excerpt="Maximum building height is 40 feet.",
        status=status,
    )

    graph.add_constraint(constraint)

    return ChangeImpactEngine(graph)


def test_detects_changed_geometry_metrics():
    engine = make_engine()

    before = {
        "building_height": 38,
        "building_footprint": 1000,
        "violations": [],
    }

    after = {
        "building_height": 38,
        "building_footprint": 1000,
        "max_height": 40,
        "violations": ["HEIGHT_VIOLATION"],
    }

    report = engine.analyze(
        "HEIGHT-001",
        before,
        after,
    )

    assert "max_height" in report["changed_metrics"]
    assert report["changed_metrics"]["max_height"]["after"] == 40
    assert report["has_changes"] is True


def test_detects_added_violations():
    engine = make_engine()

    before = {
        "violations": [],
    }

    after = {
        "violations": ["HEIGHT_VIOLATION"],
    }

    report = engine.analyze(
        "HEIGHT-001",
        before,
        after,
    )

    assert report["added_violations"] == [
        "HEIGHT_VIOLATION"
    ]
    assert report["removed_violations"] == []
    assert report["compliance_before"] is True
    assert report["compliance_after"] is False
    assert report["compliance_change"] == "became_non_compliant"


def test_detects_removed_violations():
    engine = make_engine()

    before = {
        "violations": ["HEIGHT_VIOLATION"],
    }

    after = {
        "violations": [],
    }

    report = engine.analyze(
        "HEIGHT-001",
        before,
        after,
    )

    assert report["removed_violations"] == [
        "HEIGHT_VIOLATION"
    ]
    assert report["compliance_change"] == "became_compliant"


def test_reports_unchanged_results():
    engine = make_engine()

    result = {
        "building_height": 35,
        "violations": [],
    }

    report = engine.analyze(
        "HEIGHT-001",
        result,
        result,
    )

    assert report["changed_metrics"] == {}
    assert report["added_violations"] == []
    assert report["removed_violations"] == []
    assert report["has_changes"] is False
    assert report["compliance_change"] == "remains_compliant"


def test_unverified_constraint_cannot_be_analyzed():
    engine = make_engine(
        VerificationStatus.NEEDS_HUMAN_REVIEW
    )

    with pytest.raises(ValueError):
        engine.analyze(
            "HEIGHT-001",
            {"violations": []},
            {"violations": ["HEIGHT_VIOLATION"]},
        )


def test_unknown_constraint_cannot_be_analyzed():
    engine = make_engine()

    with pytest.raises(ValueError):
        engine.analyze(
            "UNKNOWN-001",
            {"violations": []},
            {"violations": []},
        )
