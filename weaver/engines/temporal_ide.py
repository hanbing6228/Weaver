"""Bi-directional temporal DAG compiler — historical mutation with forward cascade."""

from __future__ import annotations

from typing import Any

import networkx as nx

from weaver.engines.dag_builder import LifeGraphBuilder
from weaver.models.schemas import (
    CascadeImpactRecord,
    CompileMutationResponse,
    TimelineNode,
    VariableCategory,
)


class TemporalIDEPipeline:
    """
    Compiles historical parameter mutations into downstream somatic and cognitive state.

    The pipeline walks the DAG in topological order from the mutated node forward,
    recomputing cortisol and bandwidth vectors using category-specific propagation rules.
    """

    # Category-specific attenuation when upstream stress is relieved.
    CATEGORY_ATTENUATION: dict[str, float] = {
        VariableCategory.MACRO.value: 0.55,
        VariableCategory.SOMATIC.value: 0.72,
        VariableCategory.COGNITIVE.value: 0.85,
        VariableCategory.RELATIONAL.value: 0.68,
        VariableCategory.ASSET.value: 0.40,
    }

    COGNITIVE_RELIEF_KEYS = frozenset(
        {
            "self_blame",
            "perfectionism_load",
            "rumination_index",
            "catastrophizing",
        }
    )

    SOMATIC_RELIEF_KEYS = frozenset(
        {
            "posture_compression",
            "cgm_spike_index",
            "vagal_tone_deficit",
            "sleep_debt_hours",
        }
    )

    def __init__(self, life_graph: nx.DiGraph) -> None:
        if not isinstance(life_graph, nx.DiGraph):
            raise TypeError("life_graph must be a networkx.DiGraph instance")
        if life_graph.number_of_nodes() > 0 and not nx.is_directed_acyclic_graph(life_graph):
            raise ValueError("life_graph must be a directed acyclic graph")
        self.graph = life_graph

    def compile_historical_mutation(
        self,
        target_node_id: str,
        mutated_parameters: dict[str, Any],
        *,
        mark_historical_exception: bool = True,
    ) -> CompileMutationResponse:
        """
        Overwrite historical node payload, then re-execute forward causal compilation.
        """
        if not self.graph.has_node(target_node_id):
            raise ValueError("在时空轨迹注册表中未找到该历史异常节点。")
        if not mutated_parameters:
            raise ValueError("mutated_parameters must contain at least one key")

        target_attrs = self.graph.nodes[target_node_id]
        payload: dict[str, Any] = dict(target_attrs["payload"])
        payload.update(mutated_parameters)
        if mark_historical_exception:
            payload["historical_exception"] = True
            payload["mutation_applied_at"] = mutated_parameters

        target_attrs["payload"] = payload
        target_attrs["historical_exception"] = bool(payload.get("historical_exception", False))

        downstream_nodes = LifeGraphBuilder.downstream_subgraph(self.graph, target_node_id)
        chronological_index = LifeGraphBuilder.chronological_index(self.graph)
        origin_depth = chronological_index[target_node_id]

        cascade_logs: list[CascadeImpactRecord] = []
        compile_trace: list[str] = [
            f"COMPILE_START target={target_node_id} downstream={len(downstream_nodes)}"
        ]

        relief_vector = self._compute_relief_vector(mutated_parameters)
        if relief_vector > 0.0:
            compile_trace.append(f"RELIEF_VECTOR detected magnitude={relief_vector:.4f}")

        for affected_node_id in downstream_nodes:
            record = self._evaluate_node_impact_shift(
                affected_node_id,
                relief_vector=relief_vector,
                propagation_depth=chronological_index[affected_node_id] - origin_depth,
                is_origin=affected_node_id == target_node_id,
            )
            cascade_logs.append(record)
            compile_trace.append(
                f"NODE {affected_node_id} cortisol_delta={record.cortisol_delta:.4f} "
                f"bandwidth_delta={record.bandwidth_delta:.4f}"
            )

        aggregate_cortisol_delta = sum(log.cortisol_delta for log in cascade_logs)
        somatic_clearance_nodes = sum(1 for log in cascade_logs if log.somatic_clearance)

        compile_trace.append(
            f"COMPILE_COMPLETE nodes={len(cascade_logs)} "
            f"aggregate_cortisol_delta={aggregate_cortisol_delta:.4f}"
        )

        return CompileMutationResponse(
            status="SUCCESS",
            target_node_id=target_node_id,
            compiled_nodes=len(cascade_logs),
            cascade_logs=cascade_logs,
            aggregate_cortisol_delta=aggregate_cortisol_delta,
            somatic_clearance_nodes=somatic_clearance_nodes,
            compile_trace=compile_trace,
        )

    def _compute_relief_vector(self, mutated_parameters: dict[str, Any]) -> float:
        relief = 0.0

        if mutated_parameters.get("self_blame") is False:
            relief += 0.35
        if mutated_parameters.get("perfectionism_load") is not None:
            try:
                load = float(mutated_parameters["perfectionism_load"])
                relief += max(0.0, 0.5 - load)
            except (TypeError, ValueError):
                pass
        if mutated_parameters.get("cgm_spike_index") is not None:
            try:
                spike = float(mutated_parameters["cgm_spike_index"])
                relief += max(0.0, 0.4 - spike)
            except (TypeError, ValueError):
                pass
        if mutated_parameters.get("posture_compression") is False:
            relief += 0.12
        if mutated_parameters.get("vagal_tone_deficit") is not None:
            try:
                deficit = float(mutated_parameters["vagal_tone_deficit"])
                relief += max(0.0, 0.3 - deficit)
            except (TypeError, ValueError):
                pass

        return min(relief, 1.0)

    def _evaluate_node_impact_shift(
        self,
        node_id: str,
        *,
        relief_vector: float,
        propagation_depth: int,
        is_origin: bool,
    ) -> CascadeImpactRecord:
        attrs = self.graph.nodes[node_id]
        category = str(attrs["category"])
        cortisol_before = float(attrs["cortisol_impact"])
        bandwidth_before = float(attrs["bandwidth_cost"])
        payload = dict(attrs["payload"])

        pred_cortisol, pred_bandwidth = LifeGraphBuilder.predecessor_mean_stress(self.graph, node_id)

        attenuation = self.CATEGORY_ATTENUATION.get(category, 0.60)
        depth_decay = 1.0 / (1.0 + 0.18 * propagation_depth)
        effective_relief = relief_vector * attenuation * depth_decay

        cognitive_reframe = any(
            key in payload and payload[key] in (False, 0, 0.0)
            for key in self.COGNITIVE_RELIEF_KEYS
        )
        somatic_clearance = category == VariableCategory.SOMATIC.value and (
            effective_relief > 0.08
            or any(key in payload for key in self.SOMATIC_RELIEF_KEYS)
        )

        cortisol_delta = -effective_relief * 0.65
        if cognitive_reframe and category == VariableCategory.COGNITIVE.value:
            cortisol_delta -= 0.12
        if somatic_clearance:
            cortisol_delta -= 0.08

        # Upstream mean stress bleeds into downstream nodes; relief subtracts from bleed.
        cortisol_after = self._clamp01(
            cortisol_before + cortisol_delta + (pred_cortisol * 0.12 * (1.0 - effective_relief))
        )

        bandwidth_delta = -effective_relief * 0.55
        if category == VariableCategory.MACRO.value and effective_relief > 0.2:
            bandwidth_delta -= 0.05
        bandwidth_after = self._clamp01(
            bandwidth_before + bandwidth_delta + (pred_bandwidth * 0.10 * (1.0 - effective_relief))
        )

        if is_origin:
            # Origin node receives direct payload mutation effects without depth decay penalty.
            cortisol_after = self._clamp01(cortisol_before - relief_vector * 0.45)
            bandwidth_after = self._clamp01(bandwidth_before - relief_vector * 0.38)

        attrs["cortisol_impact"] = cortisol_after
        attrs["bandwidth_cost"] = bandwidth_after
        if somatic_clearance:
            payload["somatic_clearance"] = True
            attrs["payload"] = payload

        return CascadeImpactRecord(
            node_id=node_id,
            cortisol_before=cortisol_before,
            cortisol_after=cortisol_after,
            cortisol_delta=cortisol_after - cortisol_before,
            bandwidth_before=bandwidth_before,
            bandwidth_after=bandwidth_after,
            bandwidth_delta=bandwidth_after - bandwidth_before,
            somatic_clearance=somatic_clearance,
            cognitive_reframe_applied=cognitive_reframe,
            propagation_depth=propagation_depth,
        )

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

    def export_timeline_nodes(self) -> list[TimelineNode]:
        nodes: list[TimelineNode] = []
        for node_id in nx.topological_sort(self.graph):
            attrs = self.graph.nodes[node_id]
            nodes.append(
                TimelineNode(
                    node_id=node_id,
                    timestamp=attrs["timestamp"],
                    category=VariableCategory(attrs["category"]),
                    payload=dict(attrs["payload"]),
                    cortisol_impact=float(attrs["cortisol_impact"]),
                    bandwidth_cost=float(attrs["bandwidth_cost"]),
                )
            )
        return nodes
