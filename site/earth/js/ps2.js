// ps2.js: PS2-era look for WorldForge Earth (default; ?modern=1 opts out).
// Swaps MeshStandardMaterial -> MeshLambertMaterial (per-vertex Gouraud lighting), snaps
// texture filtering to nearest (big chunky texels), and lays a CRT scanline + vignette
// overlay over the viewport. Idempotent: safe to re-run when late content (HD foliage) lands.
import * as THREE from 'three';

export function ps2ify(scene) {
  if (new URLSearchParams(location.search).get('modern') === '1') return;
  const swap = new Map();
  const conv = (m) => {
    if (!m || !(m.isMeshStandardMaterial || m.isMeshPhysicalMaterial)) return m;
    if (!swap.has(m)) {
      const l = new THREE.MeshLambertMaterial({
        map: m.map, color: m.color.clone(), vertexColors: m.vertexColors,
        emissive: (m.emissive || new THREE.Color(0)).clone(), emissiveIntensity: m.emissiveIntensity ?? 1,
        transparent: m.transparent, opacity: m.opacity, alphaTest: m.alphaTest,
        side: m.side, depthWrite: m.depthWrite });
      if (l.map) l.map.magFilter = THREE.NearestFilter;   // chunky texels, like a 4:3 era texture page
      swap.set(m, l);
    }
    return swap.get(m);
  };
  scene.traverse(o => { if (o.isMesh && o.material) o.material = Array.isArray(o.material) ? o.material.map(conv) : conv(o.material); });
  // CRT overlay: scanlines + soft vignette over the whole viewport; never intercepts input
  if (!document.getElementById('ps2-crt')) {
    const ov = document.createElement('div');
    ov.id = 'ps2-crt'; ov.setAttribute('aria-hidden', 'true');
    ov.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:3;'
      + 'background:repeating-linear-gradient(0deg,rgba(6,10,26,.08) 0 1px,transparent 1px 3px),'
      + 'radial-gradient(ellipse at center,transparent 60%,rgba(10,6,24,.32) 100%);';
    document.body.appendChild(ov);
  }
}
