"""Render binding payload shared by storyboard and legacy clients."""

from __future__ import annotations

from typing import Any

from weaver.models.schemas import VariableCategory
from weaver.services.lifecycle import WeaverLifecycleService


def build_render_bindings(service: WeaverLifecycleService) -> dict[str, Any]:
    state = service.get_current_state()
    macro_nodes = [n for n in state.nodes if n.category == VariableCategory.MACRO]
    somatic_nodes = [n for n in state.nodes if n.category == VariableCategory.SOMATIC]

    chaos_result = None
    if macro_nodes:
        chaos_result = service.evaluate_chaos(macro_nodes[0])

    avg_cortisol = sum(n.cortisol_impact for n in state.nodes) / max(len(state.nodes), 1)
    somatic_clearance = any(n.payload.get("somatic_clearance") for n in somatic_nodes)
    computed_win_rate = (
        chaos_result.computed_win_rate if chaos_result else state.asset_reserve.baseline_win_rate
    )

    return {
        "topographic_ribbon": {
            "computed_win_rate": computed_win_rate,
            "ribbon_thickness_factor": min(1.0, computed_win_rate * 1.12),
            "asset_reserve": state.asset_reserve.model_dump(by_alias=True),
        },
        "somatic_channel": {
            "VAR_SOM_CGM": next(
                (n.payload.get("cgm_spike_index", 0.0) for n in somatic_nodes),
                0.0,
            ),
            "somatic_clearance": somatic_clearance,
            "fluid_velocity_multiplier": 1.0 + (0.35 if somatic_clearance else 0.0),
        },
        "system_stress": {
            "aggregate_cortisol": avg_cortisol,
            "structural_integrity": (
                chaos_result.structural_integrity.value if chaos_result else "MONITOR"
            ),
        },
    }
