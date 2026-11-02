
from typing import Any

import networkx as nx

from core.schemas import RegulationConstraint, ConstraintType


class LivingRegulationGraph:
    """
    CODECRAFT 3D - Living Regulation Graph

    Connects:
    Document -> Evidence -> Constraint
    -> Calculation -> Geometry -> Violation
    """

    CALCULATION_MAP = {
        ConstraintType.FRONT_SETBACK: (
            "buildable_depth",
            "site_depth_minus_front_and_rear_setbacks",
        ),
        ConstraintType.REAR_SETBACK: (
            "buildable_depth",
            "site_depth_minus_front_and_rear_setbacks",
        ),
        ConstraintType.LEFT_SETBACK: (
            "buildable_width",
            "site_width_minus_left_and_right_setbacks",
        ),
        ConstraintType.RIGHT_SETBACK: (
            "buildable_width",
            "site_width_minus_left_and_right_setbacks",
        ),
        ConstraintType.MAX_HEIGHT: (
            "height_validation",
            "compare_proposed_height_with_maximum_height",
        ),
        ConstraintType.MAX_SITE_COVERAGE: (
            "coverage_validation",
            "compare_building_footprint_with_permitted_coverage",
        ),
    }

    def __init__(self):
        self.graph = nx.DiGraph()

    # --------------------------------------------------
    # ADD REGULATION CONSTRAINT
    # --------------------------------------------------

    def add_constraint(
        self,
        constraint: RegulationConstraint,
    ) -> dict[str, str]:

        document_id = f"document:{constraint.document_id}"
        evidence_id = f"evidence:{constraint.constraint_id}"
        constraint_id = f"constraint:{constraint.constraint_id}"

        calculation_name, formula = self.CALCULATION_MAP[
            constraint.constraint_type
        ]

        calculation_id = f"calculation:{calculation_name}"
        geometry_id = f"geometry:{calculation_name}"

        # 1. Document node
        self.graph.add_node(
            document_id,
            node_type="document",
            document_id=constraint.document_id,
        )

        # 2. Evidence node
        self.graph.add_node(
            evidence_id,
            node_type="evidence",
            page_number=constraint.page_number,
            clause_reference=constraint.clause_reference,
            source_excerpt=constraint.source_excerpt,
        )

        # 3. Constraint node
        self.graph.add_node(
            constraint_id,
            node_type="constraint",
            constraint_id=constraint.constraint_id,
            constraint_type=constraint.constraint_type.value,
            value=constraint.value,
            unit=constraint.unit,
            status=constraint.status.value,
            applicability=constraint.applicability,
            exceptions=constraint.exceptions,
            verification_notes=constraint.verification_notes,
        )

        # 4. Calculation node
        self.graph.add_node(
            calculation_id,
            node_type="calculation",
            calculation=calculation_name,
            formula=formula,
        )

        # 5. Geometry node
        self.graph.add_node(
            geometry_id,
            node_type="geometry",
            geometry_effect=calculation_name,
        )

        # 6. Connect the evidence chain
        self.graph.add_edge(
            document_id,
            evidence_id,
            relationship="contains",
        )

        self.graph.add_edge(
            evidence_id,
            constraint_id,
            relationship="supports",
        )

        self.graph.add_edge(
            constraint_id,
            calculation_id,
            relationship="constrains",
        )

        self.graph.add_edge(
            calculation_id,
            geometry_id,
            relationship="affects",
        )

        return {
            "document": document_id,
            "evidence": evidence_id,
            "constraint": constraint_id,
            "calculation": calculation_id,
            "geometry": geometry_id,
        }

    # --------------------------------------------------
    # ADD DETECTED VIOLATION
    # --------------------------------------------------

    def add_violation(
        self,
        constraint_id: str,
        violation_id: str,
        message: str,
    ) -> str:

        constraint_node = f"constraint:{constraint_id}"
        violation_node = f"violation:{violation_id}"

        if constraint_node not in self.graph:
            raise ValueError(
                f"Unknown constraint: {constraint_id}"
            )

        self.graph.add_node(
            violation_node,
            node_type="violation",
            violation_id=violation_id,
            message=message,
        )

        self.graph.add_edge(
            constraint_node,
            violation_node,
            relationship="causes",
        )

        return violation_node

    # --------------------------------------------------
    # FIND AFFECTED GEOMETRY
    # --------------------------------------------------

    def get_affected_geometry(
        self,
        constraint_id: str,
    ) -> list[str]:

        node_id = f"constraint:{constraint_id}"

        if node_id not in self.graph:
            raise ValueError(
                f"Unknown constraint: {constraint_id}"
            )

        descendants = nx.descendants(
            self.graph,
            node_id,
        )

        return sorted(
            node
            for node in descendants
            if self.graph.nodes[node].get("node_type") == "geometry"
        )

    # --------------------------------------------------
    # UPDATE VERIFICATION STATUS
    # --------------------------------------------------

    def update_constraint_status(
        self,
        constraint_id: str,
        new_status: str,
    ) -> None:

        node_id = f"constraint:{constraint_id}"

        if node_id not in self.graph:
            raise ValueError(
                f"Unknown constraint: {constraint_id}"
            )

        allowed_statuses = {
            "extracted",
            "needs_human_review",
            "verified",
            "rejected",
            "conflicting",
            "unresolved",
        }

        if new_status not in allowed_statuses:
            raise ValueError(
                f"Invalid verification status: {new_status}"
            )

        self.graph.nodes[node_id]["status"] = new_status

    # --------------------------------------------------
    # GET SOURCE-TO-GEOMETRY CHAIN
    # --------------------------------------------------

    def get_constraint_chain(
        self,
        constraint_id: str,
    ) -> dict[str, Any]:

        node_id = f"constraint:{constraint_id}"

        if node_id not in self.graph:
            raise ValueError(
                f"Unknown constraint: {constraint_id}"
            )

        ancestors = nx.ancestors(
            self.graph,
            node_id,
        )

        descendants = nx.descendants(
            self.graph,
            node_id,
        )

        return {
            "documents": sorted(
                node for node in ancestors
                if self.graph.nodes[node].get("node_type") == "document"
            ),
            "evidence": sorted(
                node for node in ancestors
                if self.graph.nodes[node].get("node_type") == "evidence"
            ),
            "constraint": node_id,
            "calculations": sorted(
                node for node in descendants
                if self.graph.nodes[node].get("node_type") == "calculation"
            ),
            "geometry": sorted(
                node for node in descendants
                if self.graph.nodes[node].get("node_type") == "geometry"
            ),
            "violations": sorted(
                node for node in descendants
                if self.graph.nodes[node].get("node_type") == "violation"
            ),
        }

    # --------------------------------------------------
    # EXPORT GRAPH
    # --------------------------------------------------

    def export(self) -> dict[str, Any]:

        return {
            "nodes": [
                {
                    "id": node_id,
                    **attributes,
                }
                for node_id, attributes
                in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    **attributes,
                }
                for source, target, attributes
                in self.graph.edges(data=True)
            ],
        }

    # --------------------------------------------------
    # GRAPH SUMMARY
    # --------------------------------------------------

    def summary(self) -> dict[str, Any]:

        node_types = (
            "document",
            "evidence",
            "constraint",
            "calculation",
            "geometry",
            "violation",
        )

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "node_types": {
                node_type: sum(
                    1
                    for _, attributes
                    in self.graph.nodes(data=True)
                    if attributes.get("node_type") == node_type
                )
                for node_type in node_types
            },
        }
