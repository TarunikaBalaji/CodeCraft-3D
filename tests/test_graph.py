
from core.schemas import (
    ConstraintType,
    RegulationConstraint,
    VerificationStatus,
)
from core.regulation_graph import LivingRegulationGraph


def make_height_constraint():
    return RegulationConstraint(
        constraint_id="HEIGHT-001",
        constraint_type=ConstraintType.MAX_HEIGHT,
        value=45,
        unit="feet",
        document_id="TN-REG-001",
        page_number=12,
        clause_reference="4.2",
        source_excerpt="Maximum permitted building height is 45 feet.",
        applicability="Illustrative test constraint",
        status=VerificationStatus.NEEDS_HUMAN_REVIEW,
    )


def test_constraint_schema():
    constraint = make_height_constraint()

    assert constraint.constraint_id == "HEIGHT-001"
    assert constraint.value == 45
    assert constraint.page_number == 12
    assert constraint.status == VerificationStatus.NEEDS_HUMAN_REVIEW


def test_graph_creates_evidence_to_geometry_chain():
    graph = LivingRegulationGraph()

    nodes = graph.add_constraint(make_height_constraint())

    assert nodes["document"] == "document:TN-REG-001"
    assert nodes["evidence"] == "evidence:HEIGHT-001"
    assert nodes["constraint"] == "constraint:HEIGHT-001"
    assert nodes["calculation"] == "calculation:height_validation"
    assert nodes["geometry"] == "geometry:height_validation"

    assert graph.graph.number_of_nodes() == 5
    assert graph.graph.number_of_edges() == 4

    chain = graph.get_constraint_chain("HEIGHT-001")

    assert chain["documents"] == ["document:TN-REG-001"]
    assert chain["evidence"] == ["evidence:HEIGHT-001"]
    assert chain["geometry"] == ["geometry:height_validation"]


def test_graph_connects_violation_to_constraint():
    graph = LivingRegulationGraph()
    graph.add_constraint(make_height_constraint())

    violation_node = graph.add_violation(
        constraint_id="HEIGHT-001",
        violation_id="VIOLATION-001",
        message="Proposed building exceeds maximum permitted height.",
    )

    assert violation_node == "violation:VIOLATION-001"
    assert violation_node in graph.graph
    assert graph.graph.has_edge(
        "constraint:HEIGHT-001",
        "violation:VIOLATION-001",
    )


def test_graph_finds_affected_geometry():
    graph = LivingRegulationGraph()
    graph.add_constraint(make_height_constraint())

    affected = graph.get_affected_geometry("HEIGHT-001")

    assert affected == ["geometry:height_validation"]


def test_graph_updates_verification_status():
    graph = LivingRegulationGraph()
    graph.add_constraint(make_height_constraint())

    graph.update_constraint_status("HEIGHT-001", "verified")

    assert (
        graph.graph.nodes["constraint:HEIGHT-001"]["status"]
        == "verified"
    )


def test_graph_exports_nodes_and_relationships():
    graph = LivingRegulationGraph()
    graph.add_constraint(make_height_constraint())

    exported = graph.export()
    summary = graph.summary()

    assert len(exported["nodes"]) == 5
    assert len(exported["edges"]) == 4

    assert summary["total_nodes"] == 5
    assert summary["total_relationships"] == 4

    assert summary["node_types"]["document"] == 1
    assert summary["node_types"]["evidence"] == 1
    assert summary["node_types"]["constraint"] == 1
    assert summary["node_types"]["calculation"] == 1
    assert summary["node_types"]["geometry"] == 1
    assert summary["node_types"]["violation"] == 0
