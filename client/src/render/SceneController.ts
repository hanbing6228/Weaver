import * as THREE from "three";
import type { VisualState } from "../types";
import { palette } from "../theme";
import { RibbonMesh, createGridHelper } from "./RibbonMesh";
import { SomaticField } from "./SomaticField";

export class SceneController {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly ribbon: RibbonMesh;
  private readonly somatic: SomaticField;
  private readonly clock = new THREE.Clock();
  private visual: VisualState;
  private raf = 0;

  constructor(canvas: HTMLCanvasElement, initial: VisualState) {
    this.visual = initial;

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(palette.canvas, 1);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    this.camera.position.set(0, 0.4, 7.2);
    this.camera.lookAt(0, 0, 0);

    const ambient = new THREE.AmbientLight(0xffffff, 0.85);
    const key = new THREE.DirectionalLight(0xffffff, 0.55);
    key.position.set(2, 4, 5);
    this.scene.add(ambient, key);

    this.ribbon = new RibbonMesh();
    this.somatic = new SomaticField();
    this.scene.add(this.ribbon.mesh, this.somatic.points, createGridHelper());

    this.resize();
    window.addEventListener("resize", this.resize);
  }

  setVisualState(next: VisualState): void {
    this.visual = next;
    this.somatic.setCgmIndex(next.cgmIndex);
    this.somatic.setClearance(next.somaticClearance);
    this.somatic.setVelocity(next.fluidVelocity);
  }

  start(): void {
    const tick = (): void => {
      this.raf = requestAnimationFrame(tick);
      const elapsed = this.clock.getElapsedTime();
      this.ribbon.update(
        elapsed,
        this.visual.ribbonThickness,
        this.visual.winRate,
        this.visual.aggregateCortisol,
      );
      this.somatic.update(elapsed);
      this.renderer.render(this.scene, this.camera);
    };
    tick();
  }

  stop(): void {
    cancelAnimationFrame(this.raf);
    window.removeEventListener("resize", this.resize);
    this.ribbon.dispose();
    this.somatic.dispose();
    this.renderer.dispose();
  }

  private resize = (): void => {
    const parent = this.renderer.domElement.parentElement;
    if (!parent) return;
    const w = parent.clientWidth;
    const h = parent.clientHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  };
}
