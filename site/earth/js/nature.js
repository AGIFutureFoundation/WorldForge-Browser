// WorldForge Earth nature: instanced trees / shrubs / flowers / grass placed from real OSM land cover, all swaying in
// one shared wind field (vertex shader), plus moving water on real OSM water and rivers.
// HD hero foliage: Poly Haven CC0 glTF models, loaded from their CDN on demand (see loadHeroFoliage).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { uniforms } from './core.js';

const rng = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(1337);
// mergeGeometries needs matching attributes and all-or-none indices: normalise to non-indexed position+normal
const merge = (list) => mergeGeometries(list.map(g => { const n = g.index ? g.toNonIndexed() : g.clone();
  for (const k of Object.keys(n.attributes)) if (k !== 'position' && k !== 'normal') n.deleteAttribute(k); return n; }));
const dummy = new THREE.Object3D();

export function pip(x, z, p) {
  let c = false;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    const [xi, zi] = p[i], [xj, zj] = p[j];
    if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi + 1e-9) + xi) c = !c;
  }
  return c;
}
function bbox(p) { let a = [1e9, 1e9, -1e9, -1e9]; for (const [x, z] of p) a = [Math.min(a[0], x), Math.min(a[1], z), Math.max(a[2], x), Math.max(a[3], z)]; return a; }

// Wind: bend each vertex by its height above the instance base; one shared uniform = one wind for the world.
export function windify(mat, stiffness = 1) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = uniforms.uTime; sh.uniforms.uWind = uniforms.uWind;
    sh.vertexShader = 'uniform float uTime; uniform vec2 uWind;\n' + sh.vertexShader.replace('#include <begin_vertex>', `
      #include <begin_vertex>
      #ifdef USE_INSTANCING
        vec3 ip = instanceMatrix[3].xyz;
      #else
        vec3 ip = vec3(0.0);
      #endif
      float h = max(position.y, 0.0);
      float gust = sin(uTime * 1.7 + ip.x * 0.05 + ip.z * 0.04) * 0.6 + sin(uTime * 3.1 + ip.x * 0.11) * 0.25 + 0.9;
      transformed.xz += uWind * gust * h * h * ${(0.012 / stiffness).toFixed(4)};`);
  };
  return mat;
}

function place(group, geom, mat, pts, ground, sMin, sMax, name, hue = [0.22, 0.1], light = [0.22, 0.12]) {
  if (!pts.length) return null;
  const m = new THREE.InstancedMesh(geom, mat, pts.length); m.name = name;
  pts.forEach(([x, z], i) => {
    const s = sMin + rng() * (sMax - sMin);
    dummy.position.set(x, ground.height(x, z) - 0.1, z); dummy.rotation.set(0, rng() * 6.28, 0);
    dummy.scale.set(s, s * (0.85 + rng() * 0.3), s); dummy.updateMatrix(); m.setMatrixAt(i, dummy.matrix);
    m.setColorAt(i, new THREE.Color().setHSL(hue[0] + rng() * hue[1], 0.45 + rng() * 0.25, light[0] + rng() * light[1]));
  });
  m.castShadow = m.receiveShadow = true; group.add(m); return m;
}

export function scatterSpots(geo, H) {
  const spots = { tree: [], shrub: [], flower: [], grass: [] };
  const near = (f, x, z) => f.p.length > 2 && Math.abs(f.p[0][0] - x) < 120 && Math.abs(f.p[0][1] - z) < 120;
  const blocked = (x, z) => geo.features.building.some(f => near(f, x, z) && pip(x, z, f.p))
    || geo.features.water.some(f => f.p.length > 2 && pip(x, z, f.p));
  const fill = (polys, per100, kinds) => {
    for (const f of polys) {
      if (f.p.length < 3) continue;
      const [ax, az, bx, bz] = bbox(f.p);
      const n = Math.min(Math.round(Math.min((bx - ax) * (bz - az), 160000) / 100 * per100), 1500);
      for (let i = 0; i < n; i++) {
        const x = ax + rng() * (bx - ax), z = az + rng() * (bz - az);
        if (Math.abs(x) > H || Math.abs(z) > H || !pip(x, z, f.p) || blocked(x, z)) continue;
        spots[kinds[Math.floor(rng() * kinds.length)]].push([x, z]);
      }
    }
  };
  fill(geo.features.wood, 1.4, ['tree', 'tree', 'tree', 'shrub']);
  fill(geo.features.scrub, 1.2, ['shrub', 'shrub', 'tree', 'flower']);
  fill(geo.features.park, 1.1, ['grass', 'grass', 'flower', 'shrub', 'tree']);
  for (const [x, z] of geo.features.tree) if (Math.abs(x) < H && Math.abs(z) < H) spots.tree.push([x, z]);
  // a garden ring round the plaza so every world has greenery where people arrive
  for (let i = 0; i < 320; i++) {
    const a = rng() * 6.283, r = 30 + rng() * 45, x = Math.cos(a) * r, z = Math.sin(a) * r;
    if (!blocked(x, z)) spots[['flower', 'grass', 'shrub', 'flower', 'tree'][i % 5]].push([x, z]);
  }
  return spots;
}

export function makeVegetation(geo, ground, biome = 'temperate-forest') {
  const g = new THREE.Group(); g.name = 'vegetation';
  const spots = scatterSpots(geo, geo.half);
  const conifer = /alpine|temperate-forest/.test(biome), palm = /tropical|desert/.test(biome);
  const trunk = new THREE.CylinderGeometry(0.18, 0.32, 4, 6); trunk.translate(0, 2, 0);
  let crown;
  if (conifer) { crown = new THREE.ConeGeometry(2.2, 7, 8); crown.translate(0, 6.5, 0); }
  else if (palm) { crown = new THREE.SphereGeometry(2.6, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2.3); crown.scale(1, 0.45, 1); crown.translate(0, 6.2, 0); }
  else { crown = new THREE.IcosahedronGeometry(2.6, 1); crown.scale(1, 0.85, 1); crown.translate(0, 5.6, 0); }
  place(g, trunk, new THREE.MeshStandardMaterial({ color: 0x5b4330, roughness: 1 }), spots.tree, ground, 0.8, 1.5, 'tree-trunks', [0.07, 0.02], [0.2, 0.05]);
  place(g, crown, windify(new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true }), 2.2), spots.tree, ground, 0.8, 1.5, 'tree-crowns');
  const shrub = new THREE.IcosahedronGeometry(0.9, 0); shrub.scale(1.3, 0.8, 1.3); shrub.translate(0, 0.6, 0);
  place(g, shrub, windify(new THREE.MeshStandardMaterial({ roughness: 0.95, flatShading: true }), 1.5), spots.shrub, ground, 0.7, 1.6, 'shrubs');
  const blade = new THREE.PlaneGeometry(0.12, 0.7, 1, 3); blade.translate(0, 0.35, 0);
  const tuft = merge([0, 1, 2].map(k => blade.clone().rotateY(k * 1.05)));
  const jitter = (pts, k, r) => pts.flatMap(([x, z]) => Array.from({ length: k }, () => [x + (rng() - 0.5) * r, z + (rng() - 0.5) * r]));
  place(g, tuft, windify(new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 1 }), 0.25), jitter(spots.grass, 8, 7), ground, 0.8, 1.6, 'grass', [0.2, 0.08], [0.3, 0.1]);
  const stem = new THREE.CylinderGeometry(0.015, 0.02, 0.5, 3); stem.translate(0, 0.25, 0);
  const head = new THREE.IcosahedronGeometry(0.09, 0); head.translate(0, 0.52, 0);
  const fm = place(g, merge([stem, head]), windify(new THREE.MeshStandardMaterial({ roughness: 0.7 }), 0.3), jitter(spots.flower, 10, 4), ground, 0.8, 1.7, 'flowers');
  if (fm) { const hues = [0.0, 0.08, 0.14, 0.78, 0.9, 0.6]; for (let i = 0; i < fm.count; i++) fm.setColorAt(i, new THREE.Color().setHSL(hues[i % 6], 0.8, 0.6)); }
  g.userData.counts = { trees: spots.tree.length, shrubs: spots.shrub.length, grassTufts: spots.grass.length * 8, flowers: spots.flower.length * 10 };
  return g;
}

// ---------------------------------------------------------------- HD hero foliage (Poly Haven CC0, CDN, on demand)
export const HERO = ['shrub_04', 'shrub_02', 'fern_02', 'flower_gazania', 'flower_ursinia', 'dandelion_01', 'quiver_tree_01', 'pachira_aquatica_01'];
export async function loadHeroFoliage(scene, ground, spots = 64) {
  const loader = new GLTFLoader(), g = new THREE.Group(); g.name = 'hero-foliage (Poly Haven CC0)';
  for (const [k, id] of HERO.entries()) {
    try {
      const gl = await loader.loadAsync(`https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/${id}/${id}_1k.gltf`);
      const n = Math.ceil(spots / HERO.length);
      for (let i = 0; i < n; i++) {
        const o = gl.scene.clone(true), a = (k * n + i) * 2.399, r = 22 + (i % 7) * 3.5;
        const x = Math.cos(a) * r, z = Math.sin(a) * r;
        o.position.set(x, ground.height(x, z), z); o.rotation.y = rng() * 6.28; o.scale.setScalar(1.6 + rng() * 1.2);
        o.traverse(c => { if (c.isMesh) c.castShadow = true; });
        g.add(o);
      }
    } catch (e) { console.warn('hero foliage', id, e); }
  }
  scene.add(g); return g;
}

