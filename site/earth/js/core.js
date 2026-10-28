// WorldForge Earth core: renderer, sky, real terrain (Terrarium elevation), streamed satellite imagery, OSM buildings.
// Local metres: x = east, z = south, y = up. Origin = the world's real place.
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const clock = new THREE.Clock();
export const uniforms = { uTime: { value: 0 }, uWind: { value: new THREE.Vector2(1, 0.3) }, uWeather: { value: 'clear' } };

export function makeStage(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.55;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, 1, 0.5, 9000);
  camera.position.set(-260, 210, 320);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.maxPolarAngle = Math.PI * 0.49; controls.maxDistance = 1600;
  const sky = new Sky(); sky.scale.setScalar(6000); sky.material.depthWrite = false; sky.renderOrder = -1;
  sky.frustumCulled = false; scene.add(sky);
  const su = sky.material.uniforms;
  su.turbidity.value = 6; su.rayleigh.value = 1.4; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.8;
  const sun = new THREE.DirectionalLight(0xfff1dc, 2.6);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -420, right: 420, top: 420, bottom: -420, near: 10, far: 2000 });
  scene.add(sun, sun.target, new THREE.HemisphereLight(0xcfe6ff, 0x5a5236, 0.9));
  scene.background = new THREE.Color(0x9ec4e6);
  scene.fog = new THREE.Fog(0xb4d0ea, 900, 3200);
  const sunDir = new THREE.Vector3();
  function setSun(hour) {           // 6..18 daylight arc
    const t = (hour - 6) / 12, elev = Math.sin(Math.PI * Math.min(Math.max(t, 0.02), 0.98)) * 62 + 3;
    const az = 90 + 180 * t;
    sunDir.setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - elev), THREE.MathUtils.degToRad(az));
    su.sunPosition.value.copy(sunDir);
    sun.position.copy(sunDir).multiplyScalar(900); sun.intensity = 0.6 + 2.2 * Math.sin(THREE.MathUtils.degToRad(elev));
  }
  setSun(10.5);
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  addEventListener('resize', resize); resize();
  return { renderer, scene, camera, controls, sun, setSun, resize };
}

// ---------------------------------------------------------------- terrain
export function makeGround(geo) {
  const N = geo.n, H = geo.half, E = geo.elev, step = (2 * H) / (N - 1);
  const height = (x, z) => {
    const fx = Math.min(Math.max((x + H) / step, 0), N - 1.001), fz = Math.min(Math.max((z + H) / step, 0), N - 1.001);
    const i = Math.floor(fx), j = Math.floor(fz), ax = fx - i, az = fz - j;
    const a = E[j * N + i], b = E[j * N + i + 1], c = E[(j + 1) * N + i], d = E[(j + 1) * N + i + 1];
    return (a * (1 - ax) + b * ax) * (1 - az) + (c * (1 - ax) + d * ax) * az;
  };
  const g = new THREE.PlaneGeometry(2 * H, 2 * H, N - 1, N - 1);
  g.rotateX(-Math.PI / 2);
  const p = g.attributes.position;
  for (let k = 0; k < p.count; k++) p.setY(k, E[k]);
  g.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ color: 0x8a9a6a, roughness: 0.95 });
  const mesh = new THREE.Mesh(g, mat); mesh.receiveShadow = true; mesh.name = 'ground';
  // skirt so the square doesn't float
  const skirt = new THREE.Mesh(new THREE.BoxGeometry(2 * H, 40, 2 * H), new THREE.MeshStandardMaterial({ color: 0x4b4234 }));
  skirt.position.y = Math.min(...E) - 20.5;
  return { mesh, skirt, height, half: H };
}

// Satellite imagery is streamed at run time (never stored in the repo), with attribution shown in the HUD.
export const IMAGERY = {
  esri: { url: (z, x, y) => `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`,
          credit: 'Imagery: Esri, Maxar, Earthstar Geographics, and the GIS User Community' },
};

export async function drapeImagery(geo, ground, onProgress) {
  const H = geo.half, kx = 111320 * Math.cos(geo.lat * Math.PI / 180), kz = 110540;
  const toGeo = (x, z) => [geo.lat - z / kz, geo.lon + x / kx];
  const tileF = (lat, lon, z) => { const n = 2 ** z;
    return [(lon + 180) / 360 * n, (1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2 * n]; };
  let Z = 17, nw, se;
  for (; Z > 13; Z--) {
    nw = tileF(...toGeo(-H, -H), Z); se = tileF(...toGeo(H, H), Z);
    if ((Math.floor(se[0]) - Math.floor(nw[0]) + 1) * (Math.floor(se[1]) - Math.floor(nw[1]) + 1) <= 64) break;
  }
  const x0 = Math.floor(nw[0]), y0 = Math.floor(nw[1]), x1 = Math.floor(se[0]), y1 = Math.floor(se[1]);
  const big = document.createElement('canvas');
  big.width = (x1 - x0 + 1) * 256; big.height = (y1 - y0 + 1) * 256;
  const ctx = big.getContext('2d');
  let done = 0; const total = (x1 - x0 + 1) * (y1 - y0 + 1);
  const jobs = [];
  for (let ty = y0; ty <= y1; ty++) for (let tx = x0; tx <= x1; tx++) {
    jobs.push(new Promise((res) => {
      const img = new Image(); img.crossOrigin = 'anonymous';
      img.onload = () => { ctx.drawImage(img, (tx - x0) * 256, (ty - y0) * 256); onProgress?.(++done / total); res(); };
      img.onerror = () => { onProgress?.(++done / total); res(); };
      img.src = IMAGERY.esri.url(Z, tx, ty);
    }));
  }
  await Promise.all(jobs);
  // crop the exact square
  const out = document.createElement('canvas'); out.width = out.height = 2048;
  const sx = (nw[0] - x0) * 256, sy = (nw[1] - y0) * 256, sw = (se[0] - nw[0]) * 256, sh = (se[1] - nw[1]) * 256;
  out.getContext('2d').drawImage(big, sx, sy, sw, sh, 0, 0, 2048, 2048);
  const tex = new THREE.CanvasTexture(out);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  ground.mesh.material.map = tex; ground.mesh.material.color.set(0xffffff); ground.mesh.material.needsUpdate = true;
  return { zoom: Z, tiles: total, credit: IMAGERY.esri.credit, canvas: out };
}

// ---------------------------------------------------------------- OSM buildings (extruded footprints, real
// heights) with PROCEDURAL FACHADES: per-wall UVs, window grids / brick / glass chosen by the
// building's real height class, dark roofs. All textures drawn once on a canvas.
function facadeTex(kind) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 128;
  const x = c.getContext('2d');
  if (kind === 'glass') {
    x.fillStyle = '#7e9bb5'; x.fillRect(0, 0, 256, 128);
    for (let i = 0; i < 8; i++) for (let j = 0; j < 4; j++) {
      x.fillStyle = `rgba(14,22,34,${0.5 + Math.random() * 0.35})`;
      x.fillRect(6 + i * 31.5, 5 + j * 31, 22, 20);
      x.fillStyle = 'rgba(255,255,255,.10)'; x.fillRect(6 + i * 31.5, 5 + j * 31, 22, 4);
    }
    x.strokeStyle = '#31445a'; x.lineWidth = 2;
    for (let i = 0; i <= 8; i++) { x.beginPath(); x.moveTo(i * 31.5, 0); x.lineTo(i * 31.5, 128); x.stroke(); }
    for (let j = 0; j <= 4; j++) { x.beginPath(); x.moveTo(0, j * 31.5); x.lineTo(256, j * 31.5); x.stroke(); }
  } else if (kind === 'brick') {
    x.fillStyle = '#b28a72'; x.fillRect(0, 0, 256, 128);
    for (let y = 0; y < 128; y += 7) for (let i = 0; i < 16; i++) {
      x.fillStyle = `rgba(${120 + Math.random() * 40 | 0},${70 + Math.random() * 30 | 0},${55 + Math.random() * 25 | 0},.6)`;
      x.fillRect((i * 16 + (y % 14 ? 8 : 0)) % 256, y, 14, 6);
    }
    for (let i = 0; i < 6; i++) for (let j = 0; j < 3; j++) {
      x.fillStyle = `rgba(20,28,40,${0.55 + Math.random() * 0.3})`;
      x.fillRect(8 + i * 42, 9 + j * 42, 26, 22);
      x.fillStyle = 'rgba(255,240,210,.35)'; x.fillRect(8 + i * 42, 9 + j * 42, 26, 5);
    }
  } else {                                     // stucco / painted low-rise with storefronts
    x.fillStyle = '#cfc7b8'; x.fillRect(0, 0, 256, 128);
    for (let k = 0; k < 400; k++) { x.fillStyle = `rgba(0,0,0,${Math.random() * 0.05})`;
      x.fillRect(Math.random() * 256, Math.random() * 128, 10, 4); }
    for (let i = 0; i < 8; i++) { x.fillStyle = i % 2 ? 'rgba(34,52,74,.8)' : 'rgba(40,60,84,.75)';
      x.fillRect(4 + i * 32, 84, 24, 40); x.fillStyle = 'rgba(255,255,255,.14)'; x.fillRect(4 + i * 32, 84, 24, 6); }
    for (let i = 0; i < 6; i++) { x.fillStyle = `rgba(22,30,42,${0.5 + Math.random() * 0.3})`;
      x.fillRect(10 + i * 42, 8, 24, 16); }
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function wallUVs(g) {
  // per-vertex UVs: walls wrap windows (u = horizontal metres, v = one floor per 3.2 m); roofs tile flat.
  const p = g.attributes.position, n = g.attributes.normal, uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (Math.abs(n.getY(i)) > 0.8) uv.set([x * 0.05, z * 0.05], i * 2);
    else if (Math.abs(n.getX(i)) > Math.abs(n.getZ(i))) uv.set([z * 0.25, y * 0.3125], i * 2);
    else uv.set([x * 0.25, y * 0.3125], i * 2);
  }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

export function makeBuildings(geo, ground) {
  const palette = [0xd9d2c3, 0xc8c3b8, 0xb9b2a5, 0xe4ded2, 0xa9a39a];
  const buckets = { low: [], mid: [], tall: [] };
  let n = 0;
  for (const f of geo.features.building) {
    const p = f.p; if (p.length < 4) continue;
    const shape = new THREE.Shape(p.map(([x, z]) => new THREE.Vector2(x, -z)));
    let area = 0; for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; area += a[0] * b[1] - b[0] * a[1]; }
    area = Math.abs(area) / 2; if (area < 12) continue;
    const h = f.h || Math.min(9 + Math.sqrt(area) * 0.35, 24);
    const g = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    let minY = Infinity; for (const [x, z] of p) minY = Math.min(minY, ground.height(x, z));
    g.translate(0, minY - 0.3, 0);
    wallUVs(g);
    const c = new THREE.Color(palette[n % palette.length]);
    const pos = g.attributes.position, nor = g.attributes.normal, col = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {                     // darken roofs so window grids read as walls only
      const k = Math.abs(nor.getY(i)) > 0.8 ? 0.55 : 1;
      col[i * 3] = c.r * k; col[i * 3 + 1] = c.g * k; col[i * 3 + 2] = c.b * k;
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    buckets[h <= 8 ? 'low' : h <= 16 ? 'mid' : 'tall'].push(g.index ? g.toNonIndexed() : g); n++;
  }
  const root = new THREE.Group(); root.name = `osm-buildings (${n})`;
  const style = { low: ['stucco', 0.85, 0.02], mid: ['brick', 0.7, 0.05], tall: ['glass', 0.35, 0.45] };
  for (const [k, geos] of Object.entries(buckets)) {
    if (!geos.length) continue;
    const [kind, rough, metal] = style[k];
    const mesh = new THREE.Mesh(mergeGeometries(geos, false),
      new THREE.MeshStandardMaterial({ vertexColors: true, map: facadeTex(kind), roughness: rough, metalness: metal }));
    mesh.castShadow = mesh.receiveShadow = true; root.add(mesh);
  }
  return root.children.length ? root : null;
}
