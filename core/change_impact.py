
from typing import Any

from core.regulation_graph import LivingRegulationGraph


class ChangeImpactEngine:
    """
    Compares geometry results before and after a change
    and produces an evidence-linked impact summary.
    """

    def __init__(self, graph: LivingRegulationGraph):
        self.graph = graph

    @staticmethod
    def _to_dict(result: Any) -> dict:
        """
        Accept either a GeometryResult object or a dictionary.
        """
        if isinstance(result, dict):
            return result

        if hasattr(result, "to_dict"):
            converted = result.to_dict()

            if isinstance(converted, dict):
                return converted

        raise TypeError(
            "Geometry result must be a dictionary or provide to_dict()."
        )

    @staticmethod
    def _get_violations(result: dict) -> set[str]:
        violations = result.get("violations", [])

        if violations is None:
            return set()

        if not isinstance(violations, (list, tuple, set)):
            raise TypeError("The violations field must be a list or set.")

        return {str(item) for item in violations}

    @staticmethod
    def _compare_metrics(
        before: dict,
        after: dict,
    ) -> dict[str, dict[str, Any]]:
        """
        Compare top-level geometry metrics, excluding violations.
        """
        changed = {}

        all_keys = set(before) | set(after)

        for key in sorted(all_keys):
            if key == "violations":
                continue

            before_value = before.get(key)
            after_value = after.get(key)

            if before_value != after_value:
                changed[key] = {
                    "before": before_value,
                    "after": after_value,
                }

        return changed

    def analyze(
        self,
        changed_constraint_id: str,
        before_result: Any,
        after_result: Any,
    ) -> dict[str, Any]:
        """
        Generate a change impact report.

        The changed constraint must exist in the graph
        and have verified status.
        """

        impact = self.graph.get_affected_geometry(
            changed_constraint_id
        )

        constraint_node = f"constraint:{changed_constraint_id}"

        if constraint_node not in self.graph.graph:
            raise ValueError(
                f"Unknown constraint: {changed_constraint_id}"
            )

        status = self.graph.graph.nodes[constraint_node].get("status")

        if status != "verified":
            raise ValueError(
                "Only verified constraints can be analyzed."
            )

        before = self._to_dict(before_result)
        after = self._to_dict(after_result)

        before_violations = self._get_violations(before)
        after_violations = self._get_violations(after)

        added_violations = sorted(
            after_violations - before_violations
        )

        removed_violations = sorted(
            before_violations - after_violations
        )

        changed_metrics = self._compare_metrics(
            before,
            after,
        )

        compliance_before = len(before_violations) == 0
        compliance_after = len(after_violations) == 0

        if compliance_before and not compliance_after:
            compliance_change = "became_non_compliant"
        elif not compliance_before and compliance_after:
            compliance_change = "became_compliant"
        elif compliance_before and compliance_after:
            compliance_change = "remains_compliant"
        else:
            compliance_change = "remains_non_compliant"

        has_changes = bool(
            changed_metrics
            or added_violations
            or removed_violations
        )

        return {
            "changed_constraint_id": changed_constraint_id,
            "constraint_status": status,
            "affected_geometry": sorted(impact),
            "changed_metrics": changed_metrics,
            "added_violations": added_violations,
            "removed_violations": removed_violations,
            "compliance_before": compliance_before,
            "compliance_after": compliance_after,
            "compliance_change": compliance_change,
            "has_changes": has_changes,
        }
