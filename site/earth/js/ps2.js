// ps2.js: PS2-era look for WorldForge Earth (default; ?modern=1 opts out).
// Swaps MeshStandardMaterial -> MeshLambertMaterial (per-vertex Gouraud lighting), snaps
// texture filtering to nearest (big chunky texels), enforces the era texture page budget
// (nothing larger than 512px: the satellite drape and hero foliage get downscaled at load),
// and lays a CRT scanline + vignette overlay over the viewport. Idempotent: safe to re-run
// when late content (HD foliage) lands. Returns (and stashes on window.__wf.ps2) the stats
// ps2_probe.mjs reports: materials swapped, maps downscaled, texture megapixels before/after.
import * as THREE from 'three';

const PAGE = 512;          // era texture page ceiling (SMARTCITI-STYLE.md: 512 hero, 256 typical)

function eraizeMap(map) {
  const img = map?.image, w = img?.width || 0, h = img?.height || 0;
  if (!w || !h || (w <= PAGE && h <= PAGE)) return map;
  const s = PAGE / Math.max(w, h), dw = Math.max(2, Math.round(w * s)), dh = Math.max(2, Math.round(h * s));
  const c = document.createElement('canvas'); c.width = dw; c.height = dh;
  c.getContext('2d').drawImage(img, 0, 0, dw, dh);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = map.colorSpace; t.wrapS = map.wrapS; t.wrapT = map.wrapT;
  t.repeat.copy(map.repeat); t.offset.copy(map.offset);
  t.anisotropy = 1;                                        // PS2s had no anisotropic filtering
  map.dispose();
  return t;
}

export function ps2ify(scene) {
  if (new URLSearchParams(location.search).get('modern') === '1') return { on: false };
  const swap = new Map(); const stats = { on: true, materials: 0, mapsDownscaled: 0, mpBefore: 0, mpAfter: 0 };
  const conv = (m) => {
    if (!m || !(m.isMeshStandardMaterial || m.isMeshPhysicalMaterial)) return m;
    if (!swap.has(m)) {
      let map = m.map;
      if (map) {
        const img = map.image;
        stats.mpBefore += ((img?.width || 0) * (img?.height || 0)) / 1e6;
        map = eraizeMap(map);
        const img2 = map.image;
        stats.mpAfter += ((img2?.width || 0) * (img2?.height || 0)) / 1e6;
        if (map !== m.map) stats.mapsDownscaled++;
      }
      const l = new THREE.MeshLambertMaterial({
        map, color: m.color.clone(), vertexColors: m.vertexColors,
        emissive: (m.emissive || new THREE.Color(0)).clone(), emissiveIntensity: m.emissiveIntensity ?? 1,
        transparent: m.transparent, opacity: m.opacity, alphaTest: m.alphaTest,
        side: m.side, depthWrite: m.depthWrite });
      if (l.map) l.map.magFilter = THREE.NearestFilter;   // chunky texels, like a 4:3 era texture page
      swap.set(m, l); stats.materials++;
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
  stats.mpBefore = +stats.mpBefore.toFixed(2); stats.mpAfter = +stats.mpAfter.toFixed(2);
  return stats;
}
