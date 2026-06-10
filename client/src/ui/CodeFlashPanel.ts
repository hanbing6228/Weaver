type LineTone = "neutral" | "stress" | "success" | "final";

export class CodeFlashPanel {
  private readonly el: HTMLElement;
  private queue: string[] = [];
  private playing = false;

  constructor(rootId: string) {
    const el = document.getElementById(rootId);
    if (!el) throw new Error(`#${rootId} not found`);
    this.el = el;
  }

  clear(): void {
    this.el.textContent = "";
  }

  async playCompileTrace(trace: string[], success: boolean): Promise<void> {
    this.queue = [...trace];
    if (success) {
      this.queue.push(
        "Bug Fixed. Current Cortisol Level Reparsed successfully.",
      );
    }
    if (!this.playing) {
      await this.drain();
    }
  }

  appendChaosSummary(lines: string[]): void {
    this.queue.push(...lines);
    if (!this.playing) void this.drain();
  }

  private async drain(): Promise<void> {
    this.playing = true;
    this.clear();

    for (let i = 0; i < this.queue.length; i += 1) {
      const line = this.queue[i];
      const tone = this.toneFor(line, i);
      const row = document.createElement("div");
      row.className = `flash-line tone-${tone}`;
      row.textContent = line;
      this.el.appendChild(row);
      this.el.scrollTop = this.el.scrollHeight;
      await sleep(tone === "final" ? 120 : 28);
    }

    this.queue = [];
    this.playing = false;
  }

  private toneFor(line: string, index: number): LineTone {
    if (line.startsWith("Bug Fixed")) return "final";
    if (line.includes("COMPILE_START")) return "neutral";
    if (line.includes("cortisol_delta") && line.includes("-")) return "success";
    if (line.includes("RELIEF") || line.includes("COMPILE_COMPLETE")) {
      return "success";
    }
    if (index < 3) return "stress";
    return "neutral";
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function injectCodeFlashStyles(): void {
  const style = document.createElement("style");
  style.textContent = `
    .flash-line { font-family: "IBM Plex Mono", monospace; font-size: 11px; line-height: 1.55; }
    .flash-line.tone-stress { color: #8B2635; }
    .flash-line.tone-neutral { color: #5a5a62; }
    .flash-line.tone-success { color: #2D6A4F; }
    .flash-line.tone-final { color: #2D6A4F; font-weight: 500; margin-top: 8px; }
  `;
  document.head.appendChild(style);
}
