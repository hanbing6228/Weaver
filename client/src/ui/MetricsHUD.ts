import type { VisualState } from "../types";
import { css } from "../theme";

export class MetricsHUD {
  private readonly root: HTMLElement;

  constructor(rootId: string) {
    const el = document.getElementById(rootId);
    if (!el) throw new Error(`#${rootId} not found`);
    this.root = el;
  }

  render(state: VisualState, extras?: { scheduler?: string; hsaSurvival?: number }): void {
    const integrityClass =
      state.structuralIntegrity === "ABS_SECURE" ? "ok" : "watch";

    this.root.innerHTML = `
      <div class="metric">
        <span class="label">Win Rate</span>
        <span class="value">${(state.winRate * 100).toFixed(1)}%</span>
      </div>
      <div class="metric">
        <span class="label">Ribbon σ</span>
        <span class="value">${state.ribbonThickness.toFixed(3)}</span>
      </div>
      <div class="metric">
        <span class="label">CGM Index</span>
        <span class="value">${state.cgmIndex.toFixed(2)}</span>
      </div>
      <div class="metric ${integrityClass}">
        <span class="label">Integrity</span>
        <span class="value">${state.structuralIntegrity}</span>
      </div>
      ${
        extras?.scheduler
          ? `<div class="metric"><span class="label">Scheduler</span><span class="value mono">${extras.scheduler}</span></div>`
          : ""
      }
      ${
        extras?.hsaSurvival !== undefined
          ? `<div class="metric"><span class="label">HSA Surv.</span><span class="value">${(extras.hsaSurvival * 100).toFixed(1)}%</span></div>`
          : ""
      }
    `;
  }
}

export function injectHudStyles(): void {
  const style = document.createElement("style");
  style.textContent = `
    .metrics-hud { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
    .metric { display: flex; flex-direction: column; gap: 2px; min-width: 72px; }
    .metric .label { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: #7a7a82; }
    .metric .value { font-size: 13px; font-weight: 500; color: ${css.titanium}; font-variant-numeric: tabular-nums; }
    .metric .value.mono { font-family: "IBM Plex Mono", monospace; font-size: 10px; }
    .metric.ok .value { color: ${css.emerald}; }
    .metric.watch .value { color: #8a6a2a; }
  `;
  document.head.appendChild(style);
}
