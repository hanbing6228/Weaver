"""Event-driven reactive lifecycle orchestrating DAG compile and chaos interception."""

from __future__ import annotations

from weaver.engines.dag_builder import LifeGraphBuilder
from weaver.engines.stress_engine import StructuralStressEngine
from weaver.engines.temporal_ide import TemporalIDEPipeline
from weaver.models.schemas import (
    ChaosEvaluationResult,
    CompileMutationRequest,
    CompileMutationResponse,
    GraphSnapshot,
    LifeGraphState,
    TimelineNode,
)


class WeaverLifecycleService:
    """
    Flow container service: loads graph state, routes compile events,
    and dispatches chaos vectors to the structural stress engine.
    """

    def __init__(self, state: LifeGraphState, *, monte_carlo_seed: int | None = 42) -> None:
        self.state = state
        self._builder = LifeGraphBuilder(state)
        self._pipeline = TemporalIDEPipeline(self._builder.graph)
        self._stress_engine = StructuralStressEngine(
            state.asset_reserve,
            random_seed=monte_carlo_seed,
        )

    @property
    def graph_snapshot(self) -> GraphSnapshot:
        return self._builder.snapshot()

    def compile_historical_mutation(
        self,
        request: CompileMutationRequest,
    ) -> CompileMutationResponse:
        response = self._pipeline.compile_historical_mutation(
            target_node_id=request.target_node_id,
            mutated_parameters=request.mutated_parameters,
            mark_historical_exception=request.mark_historical_exception,
        )
        self._sync_state_from_graph()
        return response

    def evaluate_chaos(self, anomaly: TimelineNode) -> ChaosEvaluationResult:
        return self._stress_engine.evaluate_chaos_impact(anomaly)

    def evaluate_compound_chaos(
        self,
        anomalies: list[TimelineNode],
    ) -> ChaosEvaluationResult:
        return self._stress_engine.evaluate_compound_chaos(anomalies)

    def get_current_state(self) -> LifeGraphState:
        return self.state

    def _sync_state_from_graph(self) -> None:
        self.state = LifeGraphState(
            nodes=self._pipeline.export_timeline_nodes(),
            tickets=self.state.tickets,
            asset_reserve=self.state.asset_reserve,
        )
