"""Monte Carlo structural stress simulation and chaos anomaly interception."""

from __future__ import annotations

from typing import Any

import numpy as np

from weaver.models.schemas import (
    AssetReserve,
    ChaosEvaluationResult,
    SchedulerOverride,
    StructuralIntegrity,
    TimelineNode,
    VariableCategory,
)


class StructuralStressEngine:
    """
    Vectorized Monte Carlo engine evaluating whether external chaos vectors
    breach HSA liquidity, retirement reserves, and zero-mortgage fortification.
    """

    DEFAULT_MONTE_CARLO_RUNS = 10_000
    HSA_LIQUIDITY_FLOOR = 12_000.0
    INTEGRITY_THRESHOLD = 0.95
    HIGH_STRESS_CORTISOL = 0.65

    CATEGORY_SHOCK_MULTIPLIER: dict[str, float] = {
        VariableCategory.MACRO.value: 1.35,
        VariableCategory.SOMATIC.value: 0.75,
        VariableCategory.COGNITIVE.value: 0.55,
        VariableCategory.RELATIONAL.value: 0.90,
        VariableCategory.ASSET.value: 1.10,
    }

    def __init__(
        self,
        asset_reserve: AssetReserve | dict[str, Any],
        *,
        monte_carlo_runs: int = DEFAULT_MONTE_CARLO_RUNS,
        random_seed: int | None = None,
    ) -> None:
        if isinstance(asset_reserve, dict):
            self.reserve = AssetReserve.model_validate(asset_reserve)
        else:
            self.reserve = asset_reserve

        self.monte_carlo_runs = monte_carlo_runs
        self._rng = np.random.default_rng(random_seed)

        self.hsa_pool = self.reserve.hsa_balance
        self.retirement_pool = self.reserve.retirement_401k
        self.has_zero_mortgage = self.reserve.has_zero_mortgage
        self.baseline_win_rate = self.reserve.baseline_win_rate

    def evaluate_chaos_impact(self, anomaly_vector: TimelineNode) -> ChaosEvaluationResult:
        """
        Try-Catch interceptor: convert crisis input into asset-layer survival statistics.
        """
        stress_load = float(anomaly_vector.cortisol_impact)
        bandwidth_drain = float(anomaly_vector.bandwidth_cost)
        category_key = anomaly_vector.category.value
        shock_multiplier = self.CATEGORY_SHOCK_MULTIPLIER.get(category_key, 1.0)

        payload_financial_drag = self._extract_payload_financial_drag(anomaly_vector.payload)
        effective_stress = min(1.0, stress_load * shock_multiplier + payload_financial_drag)

        runs = self.monte_carlo_runs
        shocks = self._rng.normal(loc=0.0, scale=0.08, size=runs)
        macro_tail = self._rng.normal(loc=0.0, scale=0.12, size=runs)

        hsa_direct_burn = effective_stress * 8000.0
        hsa_stochastic_burn = np.abs(shocks) * 2000.0
        hsa_macro_tail = np.maximum(0.0, macro_tail) * 3500.0 * effective_stress

        simulated_hsa = self.hsa_pool - hsa_direct_burn - hsa_stochastic_burn - hsa_macro_tail

        retirement_draw = (
            effective_stress * 0.045 * self.retirement_pool
            + np.abs(shocks) * 0.012 * self.retirement_pool
        )
        simulated_retirement = self.retirement_pool - retirement_draw

        hsa_survived = simulated_hsa > self.HSA_LIQUIDITY_FLOOR
        retirement_survived = simulated_retirement > (self.retirement_pool * 0.72)

        if self.has_zero_mortgage:
            structural_survived = hsa_survived & retirement_survived
        else:
            mortgage_stress = self._rng.uniform(0.0, 0.25, size=runs)
            structural_survived = (
                hsa_survived
                & retirement_survived
                & (mortgage_stress < (0.20 - effective_stress * 0.10))
            )

        hsa_survival_probability = float(np.mean(hsa_survived))
        retirement_survival_probability = float(np.mean(retirement_survived))
        calculated_integrity_probability = float(np.mean(structural_survived))

        replan_protocol = self._resolve_scheduler_override(
            stress_load=stress_load,
            bandwidth_drain=bandwidth_drain,
            integrity_probability=calculated_integrity_probability,
        )

        structural_integrity = self._classify_integrity(calculated_integrity_probability)

        return ChaosEvaluationResult(
            structural_integrity=structural_integrity,
            computed_win_rate=calculated_integrity_probability,
            win_rate_delta=calculated_integrity_probability - self.baseline_win_rate,
            engine_scheduler_override=replan_protocol,
            hsa_survival_probability=hsa_survival_probability,
            retirement_survival_probability=retirement_survival_probability,
            monte_carlo_runs=runs,
            stress_load=stress_load,
            bandwidth_drain=bandwidth_drain,
            anomaly_node_id=anomaly_vector.node_id,
        )

    def evaluate_compound_chaos(
        self,
        anomaly_vectors: list[TimelineNode],
    ) -> ChaosEvaluationResult:
        """Simulate simultaneous black-swan vectors with compounded stress load."""
        if not anomaly_vectors:
            raise ValueError("anomaly_vectors must not be empty")

        compound_stress = min(
            1.0,
            sum(float(v.cortisol_impact) for v in anomaly_vectors) * 0.72,
        )
        compound_bandwidth = min(
            1.0,
            sum(float(v.bandwidth_cost) for v in anomaly_vectors) * 0.68,
        )

        synthetic = TimelineNode(
            node_id="COMPOUND_CHAOS",
            timestamp=anomaly_vectors[0].timestamp,
            category=VariableCategory.MACRO,
            payload={
                "compound_sources": [v.node_id for v in anomaly_vectors],
                "financial_drag": sum(
                    self._extract_payload_financial_drag(v.payload) for v in anomaly_vectors
                ),
            },
            cortisol_impact=compound_stress,
            bandwidth_cost=compound_bandwidth,
        )
        result = self.evaluate_chaos_impact(synthetic)
        return result.model_copy(update={"anomaly_node_id": synthetic.node_id})

    def _extract_payload_financial_drag(self, payload: dict[str, Any]) -> float:
        drag = 0.0
        if payload.get("litigation_active"):
            drag += 0.15
        if payload.get("layoff_probability") is not None:
            try:
                drag += float(payload["layoff_probability"]) * 0.25
            except (TypeError, ValueError):
                pass
        if payload.get("medical_emergency_cost") is not None:
            try:
                cost = float(payload["medical_emergency_cost"])
                drag += min(0.30, cost / 100_000.0)
            except (TypeError, ValueError):
                pass
        if payload.get("financial_drag") is not None:
            try:
                drag += float(payload["financial_drag"])
            except (TypeError, ValueError):
                pass
        return min(drag, 0.45)

    def _resolve_scheduler_override(
        self,
        *,
        stress_load: float,
        bandwidth_drain: float,
        integrity_probability: float,
    ) -> SchedulerOverride:
        if integrity_probability < 0.80:
            return SchedulerOverride.DEFENSIVE_LIQUIDITY_LOCK
        if stress_load > self.HIGH_STRESS_CORTISOL or bandwidth_drain > 0.70:
            return SchedulerOverride.FORCE_ENGAGE_PAID_HEALING_MODE
        return SchedulerOverride.STEADY_EMISSION

    def _classify_integrity(self, probability: float) -> StructuralIntegrity:
        if probability > self.INTEGRITY_THRESHOLD:
            return StructuralIntegrity.ABS_SECURE
        if probability >= 0.75:
            return StructuralIntegrity.MONITOR
        return StructuralIntegrity.CRITICAL
