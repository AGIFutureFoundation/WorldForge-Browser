// Exercise the viewer's Access list in headless Chrome and write worldforge/out/access/{*.jpg,index.json}.
//   node worldforge/lod/access_shots.mjs [base=http://127.0.0.1:8080] [world=locator-x]
// Needs the static server (repo root) and Google Chrome. Also writes the per-world access table for every world
// (access points, interior count, steward-only count) computed from worldforge/out/<slug>/cards.json the same way
// the viewer's accessPoints() does.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const wf = path.resolve(here, '..');
const outDir = path.join(wf, 'out', 'access');
fs.mkdirSync(outDir, { recursive: true });
const [base = 'http://127.0.0.1:8080', world = 'locator-x'] = process.argv.slice(2);
const W = 1280, H = 800, port = 9341;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------------ static per-world table ----
const lmIdx = JSON.parse(fs.readFileSync(path.join(wf, 'out', 'assets', 'landmarks', 'index.json'), 'utf8'));
const lmHas = (slug) => Array.isArray(lmIdx.worlds) ? lmIdx.worlds.some((w) => w.slug === slug) : !!lmIdx.worlds?.[slug];
const pub = (c) => { const e = c.permissions?.enter; return !Array.isArray(e) || e.includes('public'); };
const worlds = {};
for (const slug of fs.readdirSync(path.join(wf, 'out')).sort()) {
  const f = path.join(wf, 'out', slug, 'cards.json');
  if (!fs.existsSync(f)) continue;
  const doc = JSON.parse(fs.readFileSync(f, 'utf8'));
  const cards = doc.cards ?? [];
  const ext = [], int = [];
  for (const k of ['plaza', 'gate']) { const c = cards.find((x) => x.kind === k); if (c) ext.push({ id: c.cardId, label: c.name, kind: k }); }
  if (lmHas(slug)) ext.push({ id: `landmark:${slug}`, label: 'Landmark', kind: 'landmark' });
  const bs = cards.filter((c) => c.building).sort((a, b) => (a.kind === 'council') - (b.kind === 'council'));
  for (const c of bs) ext.push({ id: c.cardId, label: `${c.name} · door`, kind: c.kind });
  for (const c of bs) if (c.building.interior) int.push({ id: c.cardId, label: c.kind === 'council' ? `${c.name} hall` : `${c.name} · room`, kind: c.kind, enter: c.permissions?.enter ?? ['public'], visitor: pub(c) ? 'enter' : 'view only (stewards enter)' });
  worlds[slug] = {
    access_points: ext.length + int.length, exterior: ext.length, interior_count: int.length,
    steward_only_count: cards.filter((c) => !pub(c)).length,
    steward_only_interiors: int.filter((p) => p.visitor !== 'enter').length,
    steward_only_cards: cards.filter((c) => !pub(c)).map((c) => c.cardId),
    points: { exterior: ext, interior: int },
  };
}

// ------------------------------------------------------------------ headless run ----
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wf-access-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${path.join(tmp, 'profile')}`,
  '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--hide-scrollbars', `--window-size=${W},${H}`, 'about:blank',
], { stdio: 'ignore' });
const run = { base, world, shots: [], checks: [], errors: [] };
try {
  let targets;
  for (let i = 0; i < 60 && !targets; i++) { await sleep(250); targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()).catch(() => null); }
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); pending.get(m.id)?.(m); pending.delete(m.id); });
  const send = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
  const ev = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description ?? 'eval failed'); return r.result?.result?.value; };
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Page.enable');
  const open = async (q) => {
    await send('Page.navigate', { url: `${base}/worldforge/viewer.html?world=${world}${q}` });
    for (let i = 0; i < 240; i++) { await sleep(500); if (await ev('window.__wfReady === true').catch(() => false)) return true; }
    throw new Error(`viewer not ready for ${q}`);
  };
  const shot = async (name, what) => {
    await sleep(2200);
    const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 84 });
    const f = path.join(outDir, `${name}.jpg`); fs.writeFileSync(f, Buffer.from(r.result.data, 'base64'));
    const st = await ev('JSON.stringify({ access: window.__wfAccess.state(), cam: window.__wfCam() })').then(JSON.parse);
    run.shots.push({ file: `worldforge/out/access/${name}.jpg`, bytes: fs.statSync(f).size, what, state: st });
    console.log(`${name}.jpg ${(fs.statSync(f).size / 1e3).toFixed(0)} KB · ${what}`);
    return st;
  };
  const check = (name, ok, detail) => { run.checks.push({ name, ok: !!ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`, detail ? JSON.stringify(detail) : ''); };

  await open('');
  const list = await ev('window.__wfAccess.list()');
  run.viewer_points = list;
  const zone = list.find((p) => p.inside && p.allowed && p.kind === 'zone');
  const council = list.find((p) => p.inside && p.kind === 'council');
  check('access list matches cards', list.length === worlds[world].access_points, { viewer: list.length, cards: worlds[world].access_points });
  check('council interior is view only', council && council.allowed === false, council);
  run.lod_overview = await ev('window.__wfLod()');
  check('overview uses LOD1 for the far landmark', run.lod_overview?.landmark?.lod1 && run.lod_overview.landmark.level === 0 && !run.lod_overview.landmark.near, run.lod_overview?.landmark);

  await ev(`window.__wfAccess.go(${JSON.stringify(`landmark:${world}`)}, false)`);
  await shot('exterior-landmark', 'Access → Landmark (exterior teleport, on foot)');
  await sleep(2500); run.lod_landmark_near = await ev('window.__wfLod()');
  check('landmark LOD0 streamed in near it', run.lod_landmark_near?.landmark?.near === true, run.lod_landmark_near?.landmark);

  await ev(`window.__wfAccess.go(${JSON.stringify(zone.id)}, false)`);
  const s1 = await shot('exterior-door', `Access → ${zone.label.replace(' · room', '')} · door (exterior)`);
  check('exterior teleport stays outside', s1.access.inside === null && s1.access.at === zone.id, s1.access);

  await ev(`window.__wfAccess.go(${JSON.stringify(zone.id)}, true)`);
  for (let i = 0; i < 40; i++) { if ((await ev('window.__wfAccess.state().inside')) === zone.id) break; await sleep(500); }
  const s2 = await shot('interior-room', `Access → ${zone.label} (Enter)`);
  check('interior teleport enters the room', s2.access.inside === zone.id, s2.access);

  await ev('window.__wfAccess.exit()');
  const s3 = await ev('window.__wfAccess.state()');
  check('Exit leaves the room', s3.inside === null, s3);

  await ev(`window.__wfAccess.go(${JSON.stringify(council.id)}, true)`);
  const s4 = await shot('council-denied', 'Access → Steward Council hall as a visitor: exterior + "view only (stewards enter)" note');
  check('council hall not entered by a visitor', s4.access.inside === null && s4.access.denied === council.id && /stewards enter/.test(s4.access.note ?? ''), s4.access);

  await open(`&access=${encodeURIComponent(council.id)}&inside=1`);
  const s5 = await shot('council-deeplink-denied', `deep link &access=${council.id}&inside=1`);
  check('deep link to council interior is denied', s5.access.inside === null && s5.access.denied === council.id && s5.access.result?.reason === 'stewards-only', s5.access);

  await open(`&access=${encodeURIComponent(zone.id)}&inside=1`);
  for (let i = 0; i < 40; i++) { if ((await ev('window.__wfAccess.state().inside')) === zone.id) break; await sleep(500); }
  const s6 = await shot('room-deeplink', `deep link &access=${zone.id}&inside=1`);
  check('deep link into a public room enters it', s6.access.inside === zone.id, s6.access);

  const seat = worlds[world].steward_only_cards.find((c) => c.startsWith('seat:'));
  if (seat) {
    await open(`&card=${encodeURIComponent(seat)}`);
    const s7 = await ev('JSON.stringify({ a: window.__wfAccess.state(), c: window.__wfCam() })').then(JSON.parse);
    check('seat card deep link does not put a visitor inside the council', s7.c.inside === null, s7);
  }
  run.errors = await ev('window.__errs ?? []');
  ws.close();
} catch (e) { console.error('access run failed:', e.message); run.errors.push(String(e.message)); process.exitCode = 1; }
finally { chrome.kill(); await sleep(800); try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {} }

const idx = {
  schemaVersion: 'worldforge-access/0.1', generator: 'worldforge/lod/access_shots.mjs', umbrella: 'Powered by AGI Corp',
  viewer: 'worldforge/viewer.html', url_params: { access: '<cardId> of an access point', inside: '1 = go into its room (visitors only where card.permissions.enter includes public)' },
  rule: "The viewer is a visitor. Rooms whose card gives enter: ['stewards'] (the council hall and its seats) are view only: the exterior is shown with a 'view only (stewards enter)' note.",
  totals: { worlds: Object.keys(worlds).length, access_points: Object.values(worlds).reduce((a, w) => a + w.access_points, 0), interiors: Object.values(worlds).reduce((a, w) => a + w.interior_count, 0), steward_only_interiors: Object.values(worlds).reduce((a, w) => a + w.steward_only_interiors, 0) },
  verified: { ...run, passed: run.checks.filter((c) => c.ok).length, failed: run.checks.filter((c) => !c.ok).length, at: new Date().toISOString() },
  worlds,
};
fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(idx, null, 1));
console.log(`checks: ${idx.verified.passed} passed, ${idx.verified.failed} failed · ${idx.totals.worlds} worlds in the access table`);
if (idx.verified.failed) process.exitCode = 1;
