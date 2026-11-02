
from typing import Any

from core.geometry import (
    Site,
    Setbacks,
    Building,
    calculate_geometry,
)
from core.regulation_graph import LivingRegulationGraph


class DependencyEngine:
    """
    Applies verified regulation constraints to geometry inputs
    and recalculates the building geometry.
    """

    CONSTRAINT_TO_INPUT = {
        "front_setback": "front",
        "rear_setback": "rear",
        "left_setback": "left",
        "right_setback": "right",
        "max_height": "max_height",
        "max_site_coverage": "max_coverage_percent",
    }

    def __init__(self, graph: LivingRegulationGraph):
        self.graph = graph

    def get_verified_constraints(self) -> dict[str, dict[str, Any]]:
        """
        Collect verified constraints from the regulation graph.
        """
        verified = {}

        for node_id, attributes in self.graph.graph.nodes(data=True):
            if attributes.get("node_type") != "constraint":
                continue

            if attributes.get("status") != "verified":
                continue

            constraint_type = attributes.get("constraint_type")
            value = attributes.get("value")

            if constraint_type is None or value is None:
                continue

            verified[constraint_type] = {
                "constraint_id": attributes.get("constraint_id"),
                "value": value,
                "unit": attributes.get("unit"),
            }

        return verified

    def get_constraint_impact(self, constraint_id: str) -> dict[str, Any]:
        """
        Identify which geometry dependencies are affected
        by a constraint.
        """
        constraint_node = f"constraint:{constraint_id}"

        if constraint_node not in self.graph.graph:
            raise ValueError(f"Unknown constraint: {constraint_id}")

        status = self.graph.graph.nodes[constraint_node].get("status")

        if status != "verified":
            raise ValueError(
                "Only verified constraints can trigger recalculation."
            )

        affected_geometry = self.graph.get_affected_geometry(
            constraint_id
        )

        return {
            "constraint_id": constraint_id,
            "status": status,
            "affected_geometry": affected_geometry,
            "requires_recalculation": bool(affected_geometry),
        }

    def recalculate(
        self,
        changed_constraint_id: str,
        site: Site,
        setbacks: Setbacks,
        building: Building,
        max_height: float,
        max_coverage_percent: float,
    ) -> dict[str, Any]:
        """
        Apply verified constraints and recalculate geometry.

        All dimensions and constraint values must use consistent units.
        Site coverage must be expressed as a percentage.
        """

        impact = self.get_constraint_impact(changed_constraint_id)

        if not impact["requires_recalculation"]:
            raise ValueError(
                "The changed constraint has no connected geometry dependency."
            )

        verified = self.get_verified_constraints()

        updated_setbacks = {
            "front": setbacks.front,
            "rear": setbacks.rear,
            "left": setbacks.left,
            "right": setbacks.right,
        }

        updated_max_height = max_height
        updated_max_coverage = max_coverage_percent

        applied_constraints = {}

        for constraint_type, details in verified.items():
            input_name = self.CONSTRAINT_TO_INPUT.get(constraint_type)

            if input_name is None:
                continue

            value = details["value"]

            if input_name in updated_setbacks:
                updated_setbacks[input_name] = value

            elif input_name == "max_height":
                updated_max_height = value

            elif input_name == "max_coverage_percent":
                updated_max_coverage = value

            applied_constraints[constraint_type] = {
                "constraint_id": details["constraint_id"],
                "value": value,
                "unit": details["unit"],
            }

        final_setbacks = Setbacks(**updated_setbacks)

        geometry_result = calculate_geometry(
            site=site,
            setbacks=final_setbacks,
            building=building,
            max_height=updated_max_height,
            max_coverage_percent=updated_max_coverage,
        )

        return {
            "changed_constraint_id": changed_constraint_id,
            "affected_geometry": impact["affected_geometry"],
            "applied_constraints": applied_constraints,
            "geometry_result": geometry_result,
            "geometry_result_dict": geometry_result.to_dict(),
            "recalculation_status": "completed",
        }
