// Contract check for worldforge/viewer.html, the walkable WorldForge viewer.
//   node worldforge/viewer/check.mjs --check     # one final line: "VIEWER OK: ..." or "VIEWER FAIL: ..."; exit 1 on failure
// The viewer is a static page, not a generator, so --check and a bare run are the same and nothing is written.
// It checks, without a browser:
//   1. the recording contract worldforge/review/record.mjs consumes (?world ?card ?hud=0 ?tour=1, window.__wfReady,
//      window.__wfShot for orbit | flyin | building | omega | council | landmark) and the panel's honesty strings;
//      avatars for agent, omega, coordinator and advisor cards; the row.audio HEAD-check contract; the landmark loader;
//   2. three@0.160.0 from cdn.jsdelivr.net through the importmap, and no other script origin;
//   3. the spaces shells and fit-outs still have the bounds the viewer's door and collision constants were measured
//      from (SHELL and ROOM in viewer.html); if the peer's spaces build changes them, this fails so they get re-measured;
//   4. every model the viewer loads for the 41 worlds: building exterior, room and interior, env-sky, avatar model refs,
//      civic landmark GLB and its placement (worldforge/out/assets/landmarks/index.json).
//      A missing model is reported, not failed: the viewer falls back (blockout hall, gradient sky, tinted stand-in);
//   5. the stills worldforge/out/stills/viewer-{flyin,building,omega,orbit,council,landmark}.jpg exist and are JPEGs >= 1280 px wide.
// The live counterpart (headless Chrome, three worlds) is node worldforge/viewer/record_extra.mjs verify.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..', '..');
const rel = (p) => path.join(ROOT, p);
const fails = [];
const fail = (m) => fails.push(m);

// ------------------------------------------------------------------ 1-2. the page itself
const html = fs.readFileSync(process.env.VIEWER_HTML ?? rel('worldforge/viewer.html'), 'utf8');   // VIEWER_HTML: test the check on a broken copy
const need = {
  'importmap three@0.160.0': '"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"',
  'importmap addons@0.160.0': '"three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"',
  'window.__wfReady': 'window.__wfReady = true',
  'window.__wfShot': 'window.__wfShot = (mode, t',
  '?world': "P.get('world')", '?card': "P.get('card')", '?hud=0': "P.get('hud') !== '0'", '?tour=1': "P.get('tour') === '1'",
  'tour stops the loop': 'if (!TOUR) renderer.setAnimationLoop(',
  'ACES tone mapping': 'THREE.ACESFilmicToneMapping', 'sRGB output': 'THREE.SRGBColorSpace', 'PCF soft shadows': 'THREE.PCFSoftShadowMap',
  'browser voice label': 'browser voice — the recorded synthetic line is not voiced yet',
  'HEAD check before playing': "method: 'HEAD'",
  'steward-quorum shown as held': 'held</b> for the 2-of-3 Steward Council',
  'reserved actions section': 'Held for the Steward Council (2-of-3)',
  'synthetic voice label': "an agent's voice, not a person",
  'walk eye height 1.65 m': 'EYE = 1.65',
  'pointer lock walk': 'requestPointerLock', 'touch joystick': 'id="joy"',
  'theme tokens on :root': ':root {',
  'avatars for advisor and coordinator cards': "const AV_KINDS = ['agent', 'omega', 'coordinator', 'advisor']",
  'advisor in the card list': "'coordinator', 'advisor', 'zone'",
  'intro audio from rows[].audio': 'if (e?.audio) tries.push([e.audio',
  'omega falls back to the hive greet line': 'v?.audio?.greet ?? greet?.audio',
  'recording status from the HEAD check': "ok ? 'recorded synthetic line present' : `not voiced yet",
  'advisor voice is a scripted guide': "a scripted guide's voice: not an AI model, not a person",
  'landmark index': "assets/landmarks/index.json",
  'landmark honesty line': 'synthetic civic landmark, not a real building',
};
if (html.includes('scripted, not voiced')) fail('viewer.html still hard-codes "scripted, not voiced" for the coordinator label');
const missing = Object.entries(need).filter(([, s]) => !html.includes(s)).map(([k]) => k);
for (const m of missing) fail(`viewer.html lacks ${m}`);
const MODES = ['orbit', 'flyin', 'building', 'omega', 'council', 'landmark'];
const modes = MODES.filter((m) => html.includes(`mode === '${m}'`));
if (modes.length !== MODES.length) fail(`__wfShot handles ${modes.length}/${MODES.length} modes`);
const origins = new Set([...html.matchAll(/https?:\/\/[^\s"'`)]+/g)].map((m) => new URL(m[0]).host));
const allowed = new Set(['cdn.jsdelivr.net']);
for (const o of origins) if (!allowed.has(o)) fail(`viewer.html references ${o}`);
if (/<script[^>]+src=/.test(html)) fail('viewer.html loads a script by src (it should stay a single static file)');
const num = (re) => { const m = html.match(re); return m ? m.slice(1).map(Number) : null; };
const SHELL = num(/SHELL = \{ x: ([\d.]+), zBack: (-?[\d.]+), zFront: ([\d.]+) \}/), ROOM = num(/ROOM = \{ x: ([\d.]+), z: ([\d.]+), floor: ([\d.]+) \}/);
if (!SHELL || !ROOM) fail('viewer.html SHELL/ROOM constants not found');

// ------------------------------------------------------------------ 3. measured shells
function glbBounds(file) {
  const b = fs.readFileSync(file); if (b.toString('latin1', 0, 4) !== 'glTF') throw new Error('not a GLB');
  const d = JSON.parse(b.toString('utf8', 20, 20 + b.readUInt32LE(12)));
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  const q2m = ([x, y, z, w]) => [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)];
  const local = (n) => { if (n.matrix) { const m = n.matrix; return { R: [m[0], m[4], m[8], m[1], m[5], m[9], m[2], m[6], m[10]], T: [m[12], m[13], m[14]] }; } const R = q2m(n.rotation ?? [0, 0, 0, 1]), s = n.scale ?? [1, 1, 1]; for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) R[r * 3 + c] *= s[c]; return { R, T: n.translation ?? [0, 0, 0] }; };
  const mul = (a, c) => { const R = []; for (let r = 0; r < 3; r++) for (let k = 0; k < 3; k++) R[r * 3 + k] = a.R[r * 3] * c.R[k] + a.R[r * 3 + 1] * c.R[3 + k] + a.R[r * 3 + 2] * c.R[6 + k]; return { R, T: [0, 1, 2].map((r) => a.R[r * 3] * c.T[0] + a.R[r * 3 + 1] * c.T[1] + a.R[r * 3 + 2] * c.T[2] + a.T[r]) }; };
  const walk = (i, M) => { const n = d.nodes[i], W = mul(M, local(n));
    if (n.mesh != null) for (const p of d.meshes[n.mesh].primitives) { const a = d.accessors[p.attributes.POSITION]; for (let c = 0; c < 8; c++) { const v = [0, 1, 2].map((k) => ((c >> k) & 1 ? a.max[k] : a.min[k])); for (let r = 0; r < 3; r++) { const w = W.R[r * 3] * v[0] + W.R[r * 3 + 1] * v[1] + W.R[r * 3 + 2] * v[2] + W.T[r]; lo[r] = Math.min(lo[r], w); hi[r] = Math.max(hi[r], w); } } }
    for (const ch of n.children ?? []) walk(ch, W); };
  for (const i of d.scenes[d.scene ?? 0].nodes) walk(i, { R: [1, 0, 0, 0, 1, 0, 0, 0, 1], T: [0, 0, 0] });
  return { lo, hi };
}
const index = JSON.parse(fs.readFileSync(rel('worldforge/out/index.json'), 'utf8'));
const lmIdx = fs.existsSync(rel('worldforge/out/assets/landmarks/index.json')) ? JSON.parse(fs.readFileSync(rel('worldforge/out/assets/landmarks/index.json'), 'utf8')) : null;
let landmarks = 0; const lmMissing = [];
for (const w of index.worlds) {
  const e = lmIdx ? (Array.isArray(lmIdx.worlds) ? lmIdx.worlds.find((x) => x.slug === w.slug) : lmIdx.worlds?.[w.slug]) : null;
  const f = e && `worldforge/out/assets/landmarks/${e.file ?? `${w.slug}.glb`}`;
  if (e && fs.existsSync(rel(f)) && Array.isArray(e.placement?.translation) && Number.isFinite(+e.placement?.yaw_deg)) landmarks++; else lmMissing.push(w.slug);
}
let advisorCards = 0, coordinatorCards = 0;
const shells = new Map(), rooms = new Map();
let shellsOk = 0, roomsOk = 0, models = 0, modelsMissing = [], skies = 0, avatarRefs = new Set(), avatarMissing = new Set(), doors = 0;
for (const w of index.worlds) {
  const doc = JSON.parse(fs.readFileSync(rel(`worldforge/out/${w.slug}/cards.json`), 'utf8'));
  if (fs.existsSync(rel(`my-fabric/worlds/models/env-sky-${w.slug}.glb`))) skies++;
  for (const c of doc.cards) {
    if (c.kind === 'advisor') advisorCards++; if (c.kind === 'coordinator') coordinatorCards++;
    const B = c.building;
    if (B) {
      for (const p of [B.exterior, B.room, B.interior].filter(Boolean)) { models++; if (!fs.existsSync(rel(p))) modelsMissing.push(p); }
      if (fs.existsSync(rel(B.exterior))) shells.set(B.exterior, B.door);
      if (B.interior && fs.existsSync(rel(B.interior))) rooms.set(B.interior, true);
      const dc = B.door?.centre ?? [];
      if (dc[0] === 0 && dc[1] === 0 && dc[2] === 4 && (B.door.half_width ?? 9) <= 1.3) doors++; else fail(`${c.cardId}: door ${JSON.stringify(B.door)} is not the +z door (0,0,4) the viewer places`);
    }
    if (c.avatar?.model_ref) { avatarRefs.add(c.avatar.model_ref); if (!fs.existsSync(rel(c.avatar.model_ref))) avatarMissing.add(c.avatar.model_ref); }
  }
}
const near = (a, b, tol = 0.15) => Math.abs(a - b) <= tol;
for (const [p] of shells) {
  try { const { lo, hi } = glbBounds(rel(p));
    // facade +-5.3 inside the collision box +-SHELL.x; the back wall at zBack; plinth top at y 0 (the building origin is the floor)
    if (Math.max(-lo[0], hi[0]) <= SHELL[0] + 0.05 && near(lo[2], SHELL[1], 0.1) && hi[1] > 3 && lo[1] < 0.01) shellsOk++; else fail(`${p}: bounds x ${lo[0].toFixed(2)}..${hi[0].toFixed(2)} z ${lo[2].toFixed(2)}..${hi[2].toFixed(2)} no longer match SHELL ${SHELL}; re-measure`);
  } catch (e) { fail(`${p}: ${e.message}`); }
}
for (const [p] of rooms) {
  try { const { lo, hi } = glbBounds(rel(p));
    if (near(Math.max(-lo[0], hi[0]), ROOM[0], 0.12) && near(Math.max(-lo[2], hi[2]), ROOM[1], 0.12) && near(lo[1], 0, 0.02)) roomsOk++; else fail(`${p}: bounds x +-${Math.max(-lo[0], hi[0]).toFixed(2)} z +-${Math.max(-lo[2], hi[2]).toFixed(2)} no longer match ROOM ${ROOM}; re-measure`);
  } catch (e) { fail(`${p}: ${e.message}`); }
}

// ------------------------------------------------------------------ 5. stills
function jpegSize(file) {
  const b = fs.readFileSync(file); if (b[0] !== 0xff || b[1] !== 0xd8) return null;
  for (let i = 2; i < b.length - 9;) { if (b[i] !== 0xff) { i++; continue; } const m = b[i + 1]; const len = b.readUInt16BE(i + 2); if (m >= 0xc0 && m <= 0xc3) return [b.readUInt16BE(i + 7), b.readUInt16BE(i + 5)]; i += 2 + len; }
  return null;
}
const stills = MODES.map((m) => `worldforge/out/stills/viewer-${m}.jpg`);
let stillsOk = 0;
for (const s of stills) { if (!fs.existsSync(rel(s))) { fail(`${s} missing`); continue; } const wh = jpegSize(rel(s)); if (!wh || wh[0] < 1280) fail(`${s}: ${wh ? wh.join('x') : 'not a JPEG'}`); else stillsOk++; }

const summary = `${modes.length}/${MODES.length} shot modes, ${index.worlds.length} worlds, ${models - modelsMissing.length}/${models} building models present (${shellsOk}/${shells.size} shells and ${roomsOk}/${rooms.size} fit-outs match the measured door and walls), ${doors} +z doors, ${skies}/${index.worlds.length} skies, ${avatarRefs.size - avatarMissing.size}/${avatarRefs.size} avatar roles built (${advisorCards} advisor and ${coordinatorCards} coordinator cards placed from their cards), ${landmarks}/${index.worlds.length} landmarks with GLB and placement, ${stillsOk}/${stills.length} stills`;
if (fails.length) { for (const f of fails.slice(0, 12)) console.log(`  ${f}`); console.log(`VIEWER FAIL: ${fails.length} problems (${summary})`); process.exit(1); }
console.log(`VIEWER OK: ${summary}${modelsMissing.length ? `; ${modelsMissing.length} models missing fall back to blockout` : ''}${lmMissing.length ? `; no landmark for ${lmMissing.join(', ')} (the viewer notes it)` : ''}`);
