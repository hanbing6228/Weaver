import type {
  ChaosEvaluationResult,
  CompileMutationResponse,
  RenderBindings,
} from "./types";

const API = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchRenderBindings(): Promise<RenderBindings> {
  return request<RenderBindings>("/render-bindings");
}

export function compileHistoricalMutation(): Promise<CompileMutationResponse> {
  return request<CompileMutationResponse>("/compile/historical-mutation", {
    method: "POST",
    body: JSON.stringify({
      target_node_id: "node_cognitive_perfectionism",
      mutated_parameters: { self_blame: false, perfectionism_load: 0.18 },
      mark_historical_exception: true,
    }),
  });
}

export function evaluateChaos(): Promise<ChaosEvaluationResult> {
  return request<ChaosEvaluationResult>("/chaos/evaluate", {
    method: "POST",
    body: JSON.stringify({
      node_id: "node_macro_layoff_risk",
      timestamp: new Date().toISOString(),
      category: "MACRO_SHOCK",
      payload: { layoff_probability: 0.35 },
      cortisol_impact: 0.62,
      bandwidth_cost: 0.58,
    }),
  });
}
