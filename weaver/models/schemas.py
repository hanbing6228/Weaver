"""Pydantic v2 strongly-typed domain schemas for Weaver.AI."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VariableCategory(str, Enum):
    MACRO = "MACRO_SHOCK"
    SOMATIC = "SOMATIC_BIOLOGY"
    COGNITIVE = "COGNITIVE_SHIFT"
    RELATIONAL = "RELATIONAL_FLOW"
    ASSET = "FINANCIAL_ASSET"


class LifeTicketStatus(str, Enum):
    BACKLOG = "BACKLOG"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class StructuralIntegrity(str, Enum):
    ABS_SECURE = "ABS_SECURE"
    MONITOR = "MONITOR"
    CRITICAL = "CRITICAL"


class SchedulerOverride(str, Enum):
    STEADY_EMISSION = "STEADY_EMISSION"
    FORCE_ENGAGE_PAID_HEALING_MODE = "FORCE_ENGAGE_PAID_HEALING_MODE"
    DEFENSIVE_LIQUIDITY_LOCK = "DEFENSIVE_LIQUIDITY_LOCK"


class TimelineNode(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    node_id: str = Field(..., min_length=1, description="Unique hash of the life event/state")
    timestamp: datetime
    category: VariableCategory
    payload: dict[str, Any] = Field(default_factory=dict)
    cortisol_impact: float = Field(..., ge=0.0, le=1.0, description="Stress vector load")
    bandwidth_cost: float = Field(..., ge=0.0, le=1.0, description="ADHD energy drain index")

    @field_validator("payload")
    @classmethod
    def payload_must_be_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("payload must be a JSON object")
        return value


class LifeTicket(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    ticket_id: str = Field(..., min_length=1)
    parent_node_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = ""
    status: LifeTicketStatus = LifeTicketStatus.BACKLOG
    win_contribution: float = Field(..., ge=0.001, le=1.0)
    dependencies: list[str] = Field(default_factory=list)

    @field_validator("dependencies")
    @classmethod
    def dependencies_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("ticket dependencies must be unique")
        return value


class AssetReserve(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    hsa_balance: float = Field(default=52594.60, ge=0.0, alias="HSA_BALANCE")
    retirement_401k: float = Field(default=145097.31, ge=0.0, alias="RETIREMENT_401K")
    has_zero_mortgage: bool = True
    baseline_win_rate: float = Field(default=0.89, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = dict(data)
            if "hsa_balance" in normalized and "HSA_BALANCE" not in normalized:
                normalized["HSA_BALANCE"] = normalized.pop("hsa_balance")
            if "retirement_401k" in normalized and "RETIREMENT_401K" not in normalized:
                normalized["RETIREMENT_401K"] = normalized.pop("retirement_401k")
            return normalized
        return data


class CascadeImpactRecord(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    node_id: str
    cortisol_before: float = Field(..., ge=0.0, le=1.0)
    cortisol_after: float = Field(..., ge=0.0, le=1.0)
    cortisol_delta: float
    bandwidth_before: float = Field(..., ge=0.0, le=1.0)
    bandwidth_after: float = Field(..., ge=0.0, le=1.0)
    bandwidth_delta: float
    somatic_clearance: bool = False
    cognitive_reframe_applied: bool = False
    propagation_depth: int = Field(..., ge=0)


class CompileMutationRequest(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    target_node_id: str = Field(..., min_length=1)
    mutated_parameters: dict[str, Any] = Field(..., min_length=1)
    mark_historical_exception: bool = True


class CompileMutationResponse(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    status: str
    target_node_id: str
    compiled_nodes: int
    cascade_logs: list[CascadeImpactRecord]
    aggregate_cortisol_delta: float
    somatic_clearance_nodes: int
    compile_trace: list[str]


class ChaosEvaluationResult(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    structural_integrity: StructuralIntegrity
    computed_win_rate: float = Field(..., ge=0.0, le=1.0)
    win_rate_delta: float
    engine_scheduler_override: SchedulerOverride
    hsa_survival_probability: float = Field(..., ge=0.0, le=1.0)
    retirement_survival_probability: float = Field(..., ge=0.0, le=1.0)
    monte_carlo_runs: int
    stress_load: float = Field(..., ge=0.0, le=1.0)
    bandwidth_drain: float = Field(..., ge=0.0, le=1.0)
    anomaly_node_id: str


class GraphSnapshot(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    node_count: int
    edge_count: int
    topological_order: list[str]
    is_acyclic: bool


class StoryboardVariables(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    trauma: bool = True
    walk: bool = True
    mba: bool = True

    def active_keys(self) -> list[str]:
        return [key for key in ("trauma", "walk", "mba") if getattr(self, key)]

    def active_labels(self, labels: dict[str, str]) -> list[str]:
        return [labels[key] for key in self.active_keys()]


class StoryboardCaptions(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    dark: str
    bright: str


class StoryboardMetric(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    name: str
    base_value: int
    current_value: int
    unit: str = ""
    inverse: bool = True
    max_value: int = 100


class LLMJsonRequest(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    system: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    max_tokens: int = Field(default=800, ge=64, le=4096)


class StoryboardSyncRequest(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    variables: StoryboardVariables


class StoryboardSyncResponse(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    variables: StoryboardVariables
    metrics: list[StoryboardMetric]
    captions: StoryboardCaptions
    win_contribution_percent: float
    computed_win_rate: float
    structural_integrity: str
    compile_trace: list[str]
    element_visibility: dict[str, float]


class LifeGraphState(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")

    nodes: list[TimelineNode]
    tickets: list[LifeTicket] = Field(default_factory=list)
    asset_reserve: AssetReserve = Field(default_factory=AssetReserve)

    @model_validator(mode="after")
    def validate_references(self) -> LifeGraphState:
        node_ids = {node.node_id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("duplicate node_id detected in life graph state")

        for ticket in self.tickets:
            if ticket.parent_node_id not in node_ids:
                raise ValueError(
                    f"ticket {ticket.ticket_id} references unknown parent {ticket.parent_node_id}"
                )
            for dep in ticket.dependencies:
                if dep not in node_ids:
                    raise ValueError(
                        f"ticket {ticket.ticket_id} dependency {dep} not found in graph nodes"
                    )
        return self
