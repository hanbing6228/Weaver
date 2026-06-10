"""FastAPI flow container — DAG compile and chaos stress endpoints."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from weaver.config import settings
from weaver.models.schemas import (
    AssetReserve,
    ChaosEvaluationResult,
    CompileMutationRequest,
    CompileMutationResponse,
    GraphSnapshot,
    LifeGraphState,
    LifeTicket,
    LifeTicketStatus,
    TimelineNode,
    VariableCategory,
)
from weaver.services.lifecycle import WeaverLifecycleService

_service: WeaverLifecycleService | None = None
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CLIENT_DIST = _PROJECT_ROOT / settings.static_client_dir


def _bootstrap_demo_state() -> LifeGraphState:
    """Deterministic seed graph for engine verification — not a UI mock."""
    t0 = datetime(2024, 3, 15, 9, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 6, 2, 14, 30, tzinfo=timezone.utc)
    t2 = datetime(2024, 9, 18, 8, 15, tzinfo=timezone.utc)
    t3 = datetime(2025, 1, 10, 16, 45, tzinfo=timezone.utc)
    t4 = datetime(2025, 6, 10, 11, 0, tzinfo=timezone.utc)

    return LifeGraphState(
        nodes=[
            TimelineNode(
                node_id="node_cognitive_perfectionism",
                timestamp=t0,
                category=VariableCategory.COGNITIVE,
                payload={
                    "self_blame": True,
                    "perfectionism_load": 0.82,
                    "rumination_index": 0.71,
                },
                cortisol_impact=0.68,
                bandwidth_cost=0.74,
            ),
            TimelineNode(
                node_id="node_somatic_cgm",
                timestamp=t1,
                category=VariableCategory.SOMATIC,
                payload={
                    "cgm_spike_index": 0.58,
                    "posture_compression": True,
                    "vagal_tone_deficit": 0.42,
                },
                cortisol_impact=0.52,
                bandwidth_cost=0.61,
            ),
            TimelineNode(
                node_id="node_macro_layoff_risk",
                timestamp=t2,
                category=VariableCategory.MACRO,
                payload={"layoff_probability": 0.22, "sector": "technology"},
                cortisol_impact=0.48,
                bandwidth_cost=0.55,
            ),
            TimelineNode(
                node_id="node_asset_snapshot",
                timestamp=t3,
                category=VariableCategory.ASSET,
                payload={
                    "HSA_BALANCE": 52594.60,
                    "RETIREMENT_401K": 145097.31,
                    "mortgage_balance": 0.0,
                },
                cortisol_impact=0.18,
                bandwidth_cost=0.12,
            ),
            TimelineNode(
                node_id="node_relational_boundary",
                timestamp=t4,
                category=VariableCategory.RELATIONAL,
                payload={"protocol": "de_emotionalized_notice", "litigation_active": False},
                cortisol_impact=0.35,
                bandwidth_cost=0.40,
            ),
        ],
        tickets=[
            LifeTicket(
                ticket_id="ticket_posture_reset",
                parent_node_id="node_somatic_cgm",
                title="Ergonomic posture decompression",
                description="Reduce somatic compression vector",
                status=LifeTicketStatus.BACKLOG,
                win_contribution=0.018,
                dependencies=["node_cognitive_perfectionism"],
            ),
        ],
        asset_reserve=AssetReserve(),
    )


def _ensure_service() -> WeaverLifecycleService:
    global _service
    if _service is None:
        _service = WeaverLifecycleService(
            _bootstrap_demo_state(),
            monte_carlo_seed=settings.monte_carlo_seed,
        )
    return _service


def get_service() -> WeaverLifecycleService:
    return _ensure_service()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _ensure_service()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "weaver-core"}


@app.get(f"{settings.api_prefix}/graph/snapshot", response_model=GraphSnapshot)
def graph_snapshot() -> GraphSnapshot:
    return get_service().graph_snapshot


@app.get(f"{settings.api_prefix}/state", response_model=LifeGraphState)
def get_state() -> LifeGraphState:
    return get_service().get_current_state()


@app.post(f"{settings.api_prefix}/state", response_model=LifeGraphState)
def load_state(state: LifeGraphState) -> LifeGraphState:
    global _service
    _service = WeaverLifecycleService(
        state,
        monte_carlo_seed=settings.monte_carlo_seed,
    )
    return _service.get_current_state()


@app.post(
    f"{settings.api_prefix}/compile/historical-mutation",
    response_model=CompileMutationResponse,
)
def compile_historical_mutation(
    request: CompileMutationRequest,
) -> CompileMutationResponse:
    try:
        return get_service().compile_historical_mutation(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    f"{settings.api_prefix}/chaos/evaluate",
    response_model=ChaosEvaluationResult,
)
def evaluate_chaos(anomaly: TimelineNode) -> ChaosEvaluationResult:
    return get_service().evaluate_chaos(anomaly)


@app.post(
    f"{settings.api_prefix}/chaos/evaluate-compound",
    response_model=ChaosEvaluationResult,
)
def evaluate_compound_chaos(anomalies: list[TimelineNode]) -> ChaosEvaluationResult:
    try:
        return get_service().evaluate_compound_chaos(anomalies)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(f"{settings.api_prefix}/render-bindings")
def render_bindings() -> dict[str, Any]:
    """
    Client WebGL binding payload — maps engine outputs to topographic ribbon variables.
    """
    service = get_service()
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


def _mount_client_assets(application: FastAPI) -> None:
    if not _CLIENT_DIST.is_dir():
        return

    application.mount(
        "/assets",
        StaticFiles(directory=_CLIENT_DIST / "assets"),
        name="client-assets",
    )

    @application.get("/", include_in_schema=False)
    def client_index() -> FileResponse:
        return FileResponse(_CLIENT_DIST / "index.html")


_mount_client_assets(app)
