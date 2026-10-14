// Moving water on real OSM water polygons, river centrelines and (for coastal worlds) sea level.
import * as THREE from 'three';
import { uniforms } from './core.js';

const VS = `uniform float uTime; varying vec3 vW; void main(){ vec3 p = position;
  vec4 w = modelMatrix*vec4(p,1.0); w.y += sin(w.x*0.08+uTime*1.3)*0.16 + sin(w.z*0.11+uTime*0.9)*0.12; vW = w.xyz;
  gl_Position = projectionMatrix*viewMatrix*w; }`;
const FS = `uniform float uTime; uniform vec2 uFlow; uniform vec3 uSun; varying vec3 vW;
  float n(vec2 q){ return sin(q.x)*sin(q.y); }
  void main(){ vec2 q = vW.xz*0.12 + uFlow*uTime*0.8;
    float r = n(q)+0.5*n(q*2.3+uTime*0.5)+0.25*n(q*5.1-uTime*0.8);
    vec3 N = normalize(vec3(r*0.12, 1.0, 0.12*n(q.yx*1.9)));
    vec3 V = normalize(cameraPosition - vW); float fres = pow(1.0-max(dot(N,V),0.0), 4.0);
    float spec = pow(max(dot(reflect(-normalize(uSun),N),V),0.0), 160.0);
    vec3 deep = vec3(0.05,0.17,0.22), sky = vec3(0.55,0.72,0.86);
    gl_FragColor = vec4(mix(deep, sky, 0.18+0.55*fres)+spec*0.6, 0.86); }`;

export function makeWater(geo, ground, sunDir, flow = 0.4) {
  const g = new THREE.Group(); g.name = 'water';
  const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS, transparent: true, side: THREE.DoubleSide,
    uniforms: { uTime: uniforms.uTime, uFlow: { value: new THREE.Vector2(flow, flow * 0.3) }, uSun: { value: sunDir } } });
  let polys = 0, rivers = 0;
  for (const f of geo.features.water) {
    if (f.p.length < 4) continue;
    const s = new THREE.ShapeGeometry(new THREE.Shape(f.p.map(([x, z]) => new THREE.Vector2(x, -z))), 4);
    s.rotateX(-Math.PI / 2);
    let lo = Infinity; for (const [x, z] of f.p) lo = Math.min(lo, ground.height(x, z));
    const m = new THREE.Mesh(s, mat); m.position.y = lo + 0.25; g.add(m); polys++;
  }
  for (const f of geo.features.river) {
    const H = geo.half - 2;
    const inside = f.p.filter(([x, z]) => Math.abs(x) < H && Math.abs(z) < H);   // clip to the map square
    if (inside.length < 2) continue;
    const pts = inside.map(([x, z]) => new THREE.Vector3(x, ground.height(x, z) + 0.25, z));
    const tube = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), Math.max(8, pts.length * 3), f.w / 2, 6, false);
    const m = new THREE.Mesh(tube, mat); m.scale.y = 0.15; m.position.y = pts.reduce((a, p) => a + p.y, 0) / pts.length * 0.85;
    g.add(m); rivers++;
  }
  let sea = false;
  if (geo.sea !== null && geo.sea !== undefined && Math.min(...geo.elev) < geo.sea + 1) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(2 * geo.half, 2 * geo.half).rotateX(-Math.PI / 2), mat);
    m.position.y = geo.sea + 0.2; m.name = 'sea'; g.add(m); sea = true;
  }
  g.userData.counts = { polys, rivers, sea };
  return g;
}
