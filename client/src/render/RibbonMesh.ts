import * as THREE from "three";
import { palette } from "../theme";

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  varying float vAlong;
  void main() {
    vUv = uv;
    vAlong = position.x * 0.08 + 0.5;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  uniform float uTime;
  uniform float uThickness;
  uniform float uWinRate;
  uniform float uStress;
  varying vec2 vUv;
  varying float vAlong;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
  }

  void main() {
    float flow = uTime * 0.35;
    float ridge = noise(vec2(vAlong * 6.0 + flow, vUv.y * 4.0 - flow * 0.5));
    float band = smoothstep(0.5 - uThickness * 0.42, 0.5, vUv.y)
               * (1.0 - smoothstep(0.5, 0.5 + uThickness * 0.42, vUv.y));

    float edgeGlow = pow(band, 1.4) * (0.55 + uWinRate * 0.45);
    vec3 silver = vec3(0.78, 0.80, 0.84);
    vec3 deep = vec3(0.10, 0.10, 0.12);

    float anomaly = smoothstep(0.72, 0.95, uStress) * (1.0 - uWinRate);
    vec3 stressTint = mix(vec3(0.55, 0.16, 0.21), vec3(0.18, 0.42, 0.32), uWinRate);

    vec3 color = mix(deep, silver, edgeGlow + ridge * 0.12);
    color = mix(color, stressTint, anomaly * band * 0.35);

    float alpha = band * (0.35 + uThickness * 0.55);
    gl_FragColor = vec4(color, alpha);
  }
`;

export class RibbonMesh {
  readonly mesh: THREE.Mesh;
  private readonly material: THREE.ShaderMaterial;

  constructor() {
    const geometry = new THREE.PlaneGeometry(14, 2.4, 128, 32);
    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uThickness: { value: 0.5 },
        uWinRate: { value: 0.89 },
        uStress: { value: 0.4 },
      },
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    this.mesh = new THREE.Mesh(geometry, this.material);
    this.mesh.position.y = 0.15;
  }

  update(
    elapsed: number,
    thickness: number,
    winRate: number,
    stress: number,
  ): void {
    this.material.uniforms.uTime.value = elapsed;
    this.material.uniforms.uThickness.value = THREE.MathUtils.lerp(
      this.material.uniforms.uThickness.value,
      thickness,
      0.06,
    );
    this.material.uniforms.uWinRate.value = THREE.MathUtils.lerp(
      this.material.uniforms.uWinRate.value,
      winRate,
      0.05,
    );
    this.material.uniforms.uStress.value = THREE.MathUtils.lerp(
      this.material.uniforms.uStress.value,
      stress,
      0.04,
    );
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
  }
}

export function createGridHelper(): THREE.GridHelper {
  const grid = new THREE.GridHelper(16, 32, palette.grid, palette.grid);
  grid.position.y = -1.2;
  const mat = grid.material as THREE.Material;
  mat.transparent = true;
  mat.opacity = 0.35;
  return grid;
}
