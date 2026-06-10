"""NetworkX DAG construction, validation, and serialization for life graphs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import networkx as nx

from weaver.models.schemas import (
    GraphSnapshot,
    LifeGraphState,
    LifeTicket,
    TimelineNode,
    VariableCategory,
)


class LifeGraphBuilder:
    """Builds and validates a directed acyclic life-causality graph."""

    # Temporal edges connect chronologically adjacent nodes within the same causal chain.
    TEMPORAL_EDGE_WEIGHT = 1.0
    TICKET_EDGE_WEIGHT = 0.85

    def __init__(self, state: LifeGraphState) -> None:
        self.state = state
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        graph: nx.DiGraph = nx.DiGraph()
        sorted_nodes = sorted(self.state.nodes, key=lambda n: n.timestamp)

        for node in sorted_nodes:
            graph.add_node(
                node.node_id,
                timestamp=node.timestamp,
                category=node.category.value,
                payload=dict(node.payload),
                cortisol_impact=node.cortisol_impact,
                bandwidth_cost=node.bandwidth_cost,
                historical_exception=bool(node.payload.get("historical_exception", False)),
            )

        self._add_temporal_edges(graph, sorted_nodes)
        self._add_ticket_edges(graph, self.state.tickets)
        self._validate_acyclic(graph)
        return graph

    def _add_temporal_edges(self, graph: nx.DiGraph, sorted_nodes: list[TimelineNode]) -> None:
        for prev, curr in zip(sorted_nodes, sorted_nodes[1:]):
            graph.add_edge(
                prev.node_id,
                curr.node_id,
                edge_type="TEMPORAL",
                weight=self.TEMPORAL_EDGE_WEIGHT,
            )

    def _add_ticket_edges(self, graph: nx.DiGraph, tickets: list[LifeTicket]) -> None:
        for ticket in tickets:
            for dep_id in ticket.dependencies:
                graph.add_edge(
                    dep_id,
                    ticket.parent_node_id,
                    edge_type="TICKET_DEPENDENCY",
                    ticket_id=ticket.ticket_id,
                    weight=self.TICKET_EDGE_WEIGHT,
                )

    def _validate_acyclic(self, graph: nx.DiGraph) -> None:
        if not nx.is_directed_acyclic_graph(graph):
            cycle = nx.find_cycle(graph, orientation="original")
            cycle_path = " -> ".join(f"{u}->{v}" for u, v, _ in cycle)
            raise ValueError(f"life graph contains directed cycle: {cycle_path}")

    def snapshot(self) -> GraphSnapshot:
        order = list(nx.topological_sort(self.graph))
        return GraphSnapshot(
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
            topological_order=order,
            is_acyclic=True,
        )

    def export_nodes(self) -> list[TimelineNode]:
        exported: list[TimelineNode] = []
        for node_id in nx.topological_sort(self.graph):
            attrs: dict[str, Any] = self.graph.nodes[node_id]
            exported.append(
                TimelineNode(
                    node_id=node_id,
                    timestamp=attrs["timestamp"],
                    category=VariableCategory(attrs["category"]),
                    payload=dict(attrs["payload"]),
                    cortisol_impact=float(attrs["cortisol_impact"]),
                    bandwidth_cost=float(attrs["bandwidth_cost"]),
                )
            )
        return exported

    @staticmethod
    def chronological_index(graph: nx.DiGraph) -> dict[str, int]:
        ordered = list(nx.topological_sort(graph))
        return {node_id: index for index, node_id in enumerate(ordered)}

    @staticmethod
    def downstream_subgraph(graph: nx.DiGraph, origin_node_id: str) -> list[str]:
        ordered = list(nx.topological_sort(graph))
        if origin_node_id not in ordered:
            raise ValueError(f"node {origin_node_id} not present in topological registry")
        start = ordered.index(origin_node_id)
        return ordered[start:]

    @staticmethod
    def predecessor_mean_stress(graph: nx.DiGraph, node_id: str) -> tuple[float, float]:
        predecessors = list(graph.predecessors(node_id))
        if not predecessors:
            return 0.0, 0.0
        cortisol_values = [float(graph.nodes[p]["cortisol_impact"]) for p in predecessors]
        bandwidth_values = [float(graph.nodes[p]["bandwidth_cost"]) for p in predecessors]
        return (
            sum(cortisol_values) / len(cortisol_values),
            sum(bandwidth_values) / len(bandwidth_values),
        )
