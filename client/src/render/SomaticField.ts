import * as THREE from "three";

const vertexShader = /* glsl */ `
  attribute float aPhase;
  attribute float aWeight;
  uniform float uTime;
  uniform float uVelocity;
  uniform float uClearance;
  varying float vDarkness;
  varying float vAlpha;

  void main() {
    vec3 pos = position;
    float swirl = sin(uTime * uVelocity + aPhase) * 0.15;
    pos.y += swirl;
    pos.x += cos(uTime * 0.6 + aPhase) * 0.08;

    float dissolve = smoothstep(0.0, 1.0, uClearance);
    vDarkness = aWeight * (1.0 - dissolve * 0.85);
    vAlpha = mix(0.55, 0.12, dissolve) * aWeight;

    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    gl_PointSize = mix(3.5, 1.8, dissolve) * (220.0 / -mv.z);
    gl_Position = projectionMatrix * mv;
  }
`;

const fragmentShader = /* glsl */ `
  uniform vec3 uDarkColor;
  uniform vec3 uClearColor;
  varying float vDarkness;
  varying float vAlpha;

  void main() {
    vec2 c = gl_PointCoord - 0.5;
    float d = 1.0 - smoothstep(0.35, 0.5, length(c));
    vec3 col = mix(uClearColor, uDarkColor, vDarkness);
    gl_FragColor = vec4(col, d * vAlpha);
  }
`;

export class SomaticField {
  readonly points: THREE.Points;
  private readonly material: THREE.ShaderMaterial;
  private clearanceTarget = 0;

  constructor(count = 1200) {
    const positions = new Float32Array(count * 3);
    const phases = new Float32Array(count);
    const weights = new Float32Array(count);

    for (let i = 0; i < count; i += 1) {
      positions[i * 3] = (Math.random() - 0.5) * 12;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 1.1 - 0.55;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.6;
      phases[i] = Math.random() * Math.PI * 2;
      weights[i] = 0.35 + Math.random() * 0.65;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aPhase", new THREE.BufferAttribute(phases, 1));
    geometry.setAttribute("aWeight", new THREE.BufferAttribute(weights, 1));

    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uVelocity: { value: 1 },
        uClearance: { value: 0 },
        uDarkColor: { value: new THREE.Color(0x2a1f24) },
        uClearColor: { value: new THREE.Color(0xd8dde6) },
      },
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.points = new THREE.Points(geometry, this.material);
    this.points.position.y = -0.35;
  }

  setCgmIndex(index: number): void {
    const darkness = Math.min(1, index * 1.1);
    this.material.uniforms.uDarkColor.value.setRGB(
      0.16 + darkness * 0.1,
      0.08 + darkness * 0.04,
      0.1 + darkness * 0.06,
    );
  }

  setClearance(active: boolean): void {
    this.clearanceTarget = active ? 1 : 0;
  }

  setVelocity(multiplier: number): void {
    this.material.uniforms.uVelocity.value = multiplier;
  }

  update(elapsed: number): void {
    this.material.uniforms.uTime.value = elapsed;
    const current = this.material.uniforms.uClearance.value as number;
    this.material.uniforms.uClearance.value = THREE.MathUtils.lerp(
      current,
      this.clearanceTarget,
      0.03,
    );
  }

  dispose(): void {
    this.points.geometry.dispose();
    this.material.dispose();
  }
}
