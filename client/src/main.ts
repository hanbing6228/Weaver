import "./styles/global.css";
import {
  compileHistoricalMutation,
  evaluateChaos,
  fetchRenderBindings,
} from "./api";
import { SceneController } from "./render/SceneController";
import { CodeFlashPanel, injectCodeFlashStyles } from "./ui/CodeFlashPanel";
import { MetricsHUD, injectHudStyles } from "./ui/MetricsHUD";
import type { RenderBindings, VisualState } from "./types";

function bindingsToVisual(b: RenderBindings): VisualState {
  return {
    winRate: b.topographic_ribbon.computed_win_rate,
    ribbonThickness: b.topographic_ribbon.ribbon_thickness_factor,
    cgmIndex: b.somatic_channel.VAR_SOM_CGM,
    somaticClearance: b.somatic_channel.somatic_clearance,
    fluidVelocity: b.somatic_channel.fluid_velocity_multiplier,
    aggregateCortisol: b.system_stress.aggregate_cortisol,
    structuralIntegrity: b.system_stress.structural_integrity,
  };
}

async function bootstrap(): Promise<void> {
  injectCodeFlashStyles();
  injectHudStyles();

  const canvas = document.getElementById("ribbon-canvas") as HTMLCanvasElement | null;
  if (!canvas) throw new Error("ribbon-canvas missing");

  const flash = new CodeFlashPanel("code-flash");
  const hud = new MetricsHUD("metrics-hud");

  const btnCompile = document.getElementById("btn-compile") as HTMLButtonElement;
  const btnChaos = document.getElementById("btn-chaos") as HTMLButtonElement;
  const btnRefresh = document.getElementById("btn-refresh") as HTMLButtonElement;

  let visual = bindingsToVisual(await fetchRenderBindings());
  const scene = new SceneController(canvas, visual);
  scene.start();
  hud.render(visual);

  const refresh = async (): Promise<VisualState> => {
    visual = bindingsToVisual(await fetchRenderBindings());
    scene.setVisualState(visual);
    hud.render(visual);
    return visual;
  };

  const setBusy = (busy: boolean): void => {
    btnCompile.disabled = busy;
    btnChaos.disabled = busy;
    btnRefresh.disabled = busy;
  };

  btnRefresh.addEventListener("click", () => {
    void refresh().catch(showError);
  });

  btnCompile.addEventListener("click", () => {
    void (async () => {
      setBusy(true);
      try {
        const result = await compileHistoricalMutation();
        visual = bindingsToVisual(await fetchRenderBindings());
        scene.setVisualState(visual);
        hud.render(visual);
        await flash.playCompileTrace(result.compile_trace, result.status === "SUCCESS");
      } finally {
        setBusy(false);
      }
    })().catch(showError);
  });

  btnChaos.addEventListener("click", () => {
    void (async () => {
      setBusy(true);
      try {
        const chaos = await evaluateChaos();
        visual = bindingsToVisual(await fetchRenderBindings());
        visual.winRate = chaos.computed_win_rate;
        visual.structuralIntegrity = chaos.structural_integrity;
        scene.setVisualState(visual);
        hud.render(visual, {
          scheduler: chaos.engine_scheduler_override,
          hsaSurvival: chaos.hsa_survival_probability,
        });
        await flash.playCompileTrace(
          [
            `CHAOS_EVAL anomaly=node_macro_layoff_risk runs=${chaos.monte_carlo_runs}`,
            `integrity=${chaos.structural_integrity} win_rate=${chaos.computed_win_rate.toFixed(4)}`,
            `delta=${chaos.win_rate_delta >= 0 ? "+" : ""}${chaos.win_rate_delta.toFixed(4)}`,
            `scheduler_override=${chaos.engine_scheduler_override}`,
          ],
          chaos.structural_integrity === "ABS_SECURE",
        );
      } finally {
        setBusy(false);
      }
    })().catch(showError);
  });
}

function showError(err: unknown): void {
  const message = err instanceof Error ? err.message : String(err);
  const panel = document.getElementById("code-flash");
  if (panel) {
    panel.innerHTML = `<div class="flash-line tone-stress">ENGINE_ERROR: ${message}</div>`;
  }
  console.error(err);
}

bootstrap().catch(showError);
