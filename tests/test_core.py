"""Core engine unit tests — DAG compile and Monte Carlo stress."""

from __future__ import annotations

from datetime import datetime, timezone

import networkx as nx
import pytest

from weaver.engines.dag_builder import LifeGraphBuilder
from weaver.engines.stress_engine import StructuralStressEngine
from weaver.engines.temporal_ide import TemporalIDEPipeline
from weaver.models.schemas import (
    AssetReserve,
    CompileMutationRequest,
    LifeGraphState,
    LifeTicket,
    TimelineNode,
    VariableCategory,
)
from weaver.services.lifecycle import WeaverLifecycleService


def _sample_state() -> LifeGraphState:
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return LifeGraphState(
        nodes=[
            TimelineNode(
                node_id="n1",
                timestamp=base,
                category=VariableCategory.COGNITIVE,
                payload={"self_blame": True, "perfectionism_load": 0.8},
                cortisol_impact=0.7,
                bandwidth_cost=0.65,
            ),
            TimelineNode(
                node_id="n2",
                timestamp=datetime(2025, 2, 1, tzinfo=timezone.utc),
                category=VariableCategory.SOMATIC,
                payload={"cgm_spike_index": 0.5, "posture_compression": True},
                cortisol_impact=0.55,
                bandwidth_cost=0.5,
            ),
            TimelineNode(
                node_id="n3",
                timestamp=datetime(2025, 3, 1, tzinfo=timezone.utc),
                category=VariableCategory.MACRO,
                payload={"layoff_probability": 0.3},
                cortisol_impact=0.45,
                bandwidth_cost=0.4,
            ),
        ],
        tickets=[
            LifeTicket(
                ticket_id="t1",
                parent_node_id="n2",
                title="Posture reset",
                win_contribution=0.02,
                dependencies=["n1"],
            )
        ],
        asset_reserve=AssetReserve(),
    )


def test_dag_is_acyclic_and_topologically_sorted() -> None:
    builder = LifeGraphBuilder(_sample_state())
    snapshot = builder.snapshot()
    assert snapshot.is_acyclic is True
    assert snapshot.node_count == 3
    assert snapshot.topological_order == ["n1", "n2", "n3"]


def test_cycle_detection_raises() -> None:
    state = _sample_state()
    state.tickets[0].dependencies = ["n3"]
    with pytest.raises(ValueError, match="directed cycle"):
        LifeGraphBuilder(state)


def test_historical_mutation_reduces_downstream_cortisol() -> None:
    builder = LifeGraphBuilder(_sample_state())
    pipeline = TemporalIDEPipeline(builder.graph)

    before = {nid: builder.graph.nodes[nid]["cortisol_impact"] for nid in builder.graph.nodes}

    response = pipeline.compile_historical_mutation(
        "n1",
        {"self_blame": False, "perfectionism_load": 0.2},
    )

    assert response.status == "SUCCESS"
    assert response.compiled_nodes == 3
    assert response.aggregate_cortisol_delta < 0

    after = {nid: builder.graph.nodes[nid]["cortisol_impact"] for nid in builder.graph.nodes}
    assert after["n1"] < before["n1"]
    assert after["n3"] <= before["n3"]


def test_missing_node_raises() -> None:
    builder = LifeGraphBuilder(_sample_state())
    pipeline = TemporalIDEPipeline(builder.graph)
    with pytest.raises(ValueError, match="未找到"):
        pipeline.compile_historical_mutation("missing", {"self_blame": False})


def test_stress_engine_monte_carlo_deterministic_with_seed() -> None:
    anomaly = TimelineNode(
        node_id="chaos_1",
        timestamp=datetime(2025, 6, 1, tzinfo=timezone.utc),
        category=VariableCategory.MACRO,
        payload={"layoff_probability": 0.4},
        cortisol_impact=0.55,
        bandwidth_cost=0.5,
    )
    engine_a = StructuralStressEngine(AssetReserve(), random_seed=99)
    engine_b = StructuralStressEngine(AssetReserve(), random_seed=99)
    result_a = engine_a.evaluate_chaos_impact(anomaly)
    result_b = engine_b.evaluate_chaos_impact(anomaly)
    assert result_a.computed_win_rate == result_b.computed_win_rate
    assert result_a.monte_carlo_runs == 10_000


def test_high_stress_triggers_healing_mode() -> None:
    anomaly = TimelineNode(
        node_id="chaos_high",
        timestamp=datetime(2025, 6, 1, tzinfo=timezone.utc),
        category=VariableCategory.MACRO,
        payload={},
        cortisol_impact=0.85,
        bandwidth_cost=0.75,
    )
    engine = StructuralStressEngine(AssetReserve(), random_seed=1)
    result = engine.evaluate_chaos_impact(anomaly)
    assert result.engine_scheduler_override.value == "FORCE_ENGAGE_PAID_HEALING_MODE"


def test_lifecycle_service_compile_syncs_state() -> None:
    service = WeaverLifecycleService(_sample_state(), monte_carlo_seed=7)
    request = CompileMutationRequest(
        target_node_id="n1",
        mutated_parameters={"self_blame": False},
    )
    response = service.compile_historical_mutation(request)
    state = service.get_current_state()
    n1 = next(n for n in state.nodes if n.node_id == "n1")
    assert response.compiled_nodes > 0
    assert n1.payload.get("historical_exception") is True
    assert n1.cortisol_impact < 0.7


def test_compound_chaos_evaluation() -> None:
    base = datetime(2025, 6, 1, tzinfo=timezone.utc)
    vectors = [
        TimelineNode(
            node_id="c1",
            timestamp=base,
            category=VariableCategory.MACRO,
            payload={"layoff_probability": 0.5},
            cortisol_impact=0.6,
            bandwidth_cost=0.5,
        ),
        TimelineNode(
            node_id="c2",
            timestamp=base,
            category=VariableCategory.RELATIONAL,
            payload={"litigation_active": True},
            cortisol_impact=0.5,
            bandwidth_cost=0.45,
        ),
    ]
    engine = StructuralStressEngine(AssetReserve(), random_seed=3)
    result = engine.evaluate_compound_chaos(vectors)
    assert result.anomaly_node_id == "COMPOUND_CHAOS"
    assert 0.0 <= result.computed_win_rate <= 1.0
