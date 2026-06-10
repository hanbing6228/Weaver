export interface RenderBindings {
  topographic_ribbon: {
    computed_win_rate: number;
    ribbon_thickness_factor: number;
    asset_reserve: Record<string, number | boolean>;
  };
  somatic_channel: {
    VAR_SOM_CGM: number;
    somatic_clearance: boolean;
    fluid_velocity_multiplier: number;
  };
  system_stress: {
    aggregate_cortisol: number;
    structural_integrity: string;
  };
}

export interface CompileMutationResponse {
  status: string;
  target_node_id: string;
  compiled_nodes: number;
  cascade_logs: Array<{
    node_id: string;
    cortisol_delta: number;
    bandwidth_delta: number;
    somatic_clearance: boolean;
  }>;
  aggregate_cortisol_delta: number;
  somatic_clearance_nodes: number;
  compile_trace: string[];
}

export interface ChaosEvaluationResult {
  structural_integrity: string;
  computed_win_rate: number;
  win_rate_delta: number;
  engine_scheduler_override: string;
  hsa_survival_probability: number;
  monte_carlo_runs: number;
}

export interface VisualState {
  winRate: number;
  ribbonThickness: number;
  cgmIndex: number;
  somaticClearance: boolean;
  fluidVelocity: number;
  aggregateCortisol: number;
  structuralIntegrity: string;
}
