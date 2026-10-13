// Headless-Chrome check and stills for the WorldForge console (same CDP pattern as tools/snap.mjs).
//   node consoles/worldforge/snap_console.mjs <outDir> [world,world,...] [base=http://127.0.0.1:8080/consoles/worldforge/]
// For each named world it writes <outDir>/wfc-<world>-top.jpg, -tree.jpg and -omega.jpg at 1440x1000, plus one phone
// still (390x844) of the first world. It then renders every world in one page, checks that the Master Card tree has one
// row per card, that no script error was thrown, and that the phone layout has no horizontal page scroll. The last line
// is "WFC snap ok: ..." or "WFC snap FAILED: ..."; exit 1 on failure. Needs the static server on :8080 and Google Chrome.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const [outDir = os.tmpdir(), worldsArg = 'locator-x,s20-cmmc', base = 'http://127.0.0.1:8080/consoles/worldforge/'] = process.argv.slice(2);
const worlds = worldsArg.split(',').filter(Boolean);
const port = 9347;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wfc-snap-'));
fs.mkdirSync(outDir, { recursive: true });
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${path.join(tmp, 'profile')}`,
  '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--hide-scrollbars', '--window-size=1440,1000', 'about:blank',
], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const problems = [];
const notes = [];
try {
  let targets;
  for (let i = 0; i < 80 && !targets; i++) { await sleep(250); targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()).catch(() => null); }
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  const exceptions = [];
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text);
    if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
  const evaluate = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
  const viewport = (w, h, mobile = false) => send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile });
  const shot = async (file) => { const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 86 }); fs.writeFileSync(file, Buffer.from(s.result.data, 'base64')); notes.push(`${path.basename(file)} ${(fs.statSync(file).size / 1e3).toFixed(0)} KB`); };
  const open = async (world) => {
    await send('Page.navigate', { url: `${base}?world=${encodeURIComponent(world)}` });
    for (let i = 0; i < 60; i++) { await sleep(250); if (await evaluate(`!!(window.WF && document.querySelector('#view .tree'))`)) break; }
    await sleep(500);
  };
  await send('Page.enable'); await send('Runtime.enable');
  await viewport(1440, 1000);
  for (const w of worlds) {
    await open(w);
    const cur = await evaluate('window.WF && WF.current()');
    if (cur !== w) problems.push(`?world=${w} opened ${cur}`);
    await evaluate('window.scrollTo(0, 0)'); await sleep(250);
    await shot(path.join(outDir, `wfc-${w}-top.jpg`));
    await evaluate(`(() => { const el = document.getElementById('hT'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 70); })()`); await sleep(300);
    await shot(path.join(outDir, `wfc-${w}-tree.jpg`));
    await evaluate(`(() => { const el = document.getElementById('hO'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 70); })()`); await sleep(900);
    await shot(path.join(outDir, `wfc-${w}-omega.jpg`));
    for (const [sec, name] of [['hG', 'gates'], ['hB', 'buildings'], ['hA', 'avatars'], ['hX', 'gaps']]) {
      await evaluate(`(() => { const el = document.getElementById('${sec}'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 70); })()`); await sleep(300);
      await shot(path.join(outDir, `wfc-${w}-${name}.jpg`));
    }
  }
  // every world: one tree row per card, the right header, buildings and avatars tables present
  const all = await evaluate(`(() => {
    const D = JSON.parse(document.getElementById('wf-data').textContent); const bad = [];
    for (const w of D.worlds) {
      WF.show(w.slug, false);
      const rows = document.querySelectorAll('#view .tree .row').length;
      const title = (document.getElementById('wTitle') || {}).textContent || '';
      const bld = document.querySelectorAll('#hB ~ .tw tbody tr').length;
      const held = document.querySelectorAll('#view .tree .pc.q').length;
      if (rows !== w.cards.length) bad.push(w.slug + ': ' + rows + ' rows for ' + w.cards.length + ' cards');
      if (!title.includes(w.name)) bad.push(w.slug + ': header ' + title);
      if (!bld) bad.push(w.slug + ': no building rows');
      if (held !== 2 * w.cards.length) bad.push(w.slug + ': ' + held + ' held cells for ' + w.cards.length + ' cards');
      if (getComputedStyle(document.documentElement).getPropertyValue('--h').trim() !== String(w.brand.hue)) bad.push(w.slug + ': skin hue not applied');
    }
    return { n: D.worlds.length, bad };
  })()`);
  if (!all) problems.push('render sweep returned nothing');
  else { notes.push(`${all.n} worlds rendered`); problems.push(...all.bad); }
  // desktop widths: every table fits its panel (no sideways scroll needed) for every world
  for (const [vw, vh] of [[1280, 800], [1440, 1000], [1920, 1080]]) {
    await viewport(vw, vh); await sleep(300);
    const fit = await evaluate(`(() => {
      const D = JSON.parse(document.getElementById('wf-data').textContent); const bad = []; let widest = [0, 0, ''];
      for (const w of D.worlds) {
        WF.show(w.slug, false);
        document.querySelectorAll('#view .tw').forEach((t) => {
          const h = (t.closest('section') || {}).querySelector ? t.closest('section').querySelector('h3').id : '?';
          if (t.scrollWidth - t.clientWidth > widest[0] - widest[1]) widest = [t.scrollWidth, t.clientWidth, w.slug + ' ' + h];
          if (t.scrollWidth > t.clientWidth + 1) bad.push(w.slug + ' ' + h + ' [' + t.clientWidth + ', ' + t.scrollWidth + ']');
        });
      }
      return { bad, widest };
    })()`);
    if (!fit) problems.push(`table fit sweep at ${vw}px returned nothing`);
    else {
      notes.push(`${vw}px: ${fit.bad.length} table(s) wider than their panel across all worlds`);
      problems.push(...fit.bad.slice(0, 6).map((b) => `at ${vw}px table wider than panel: ${b}`));
    }
  }
  await viewport(1440, 1000);
  // phone width: no horizontal page scroll on any of the named worlds
  await viewport(390, 844, true);
  for (const w of worlds) {
    await open(w);
    const ov = await evaluate('[document.documentElement.scrollWidth, window.innerWidth]');
    if (!ov || ov[0] > ov[1] + 1) problems.push(`${w} at 390px: page ${ov && ov[0]}px wide for a ${ov && ov[1]}px viewport`);
  }
  await open(worlds[0]); await evaluate('window.scrollTo(0, 0)'); await sleep(250);
  await shot(path.join(outDir, `wfc-${worlds[0]}-phone.jpg`));
  if (exceptions.length) problems.push(`${exceptions.length} script exception(s): ${exceptions[0]}`);
  ws.close();
} catch (e) { problems.push(`snap crashed: ${e.message}`); }
finally { chrome.kill(); await sleep(800); try { fs.rmSync(tmp, { recursive: true, force: true }); } catch { /* ignore */ } }
for (const n of notes) console.log('  ' + n);
for (const p of problems.slice(0, 20)) console.log('  problem: ' + p);
console.log(problems.length ? `WFC snap FAILED: ${problems.length} problem(s)` : `WFC snap ok: ${worlds.length} worlds shot, every world rendered, phone width fits`);
process.exit(problems.length ? 1 : 0);
