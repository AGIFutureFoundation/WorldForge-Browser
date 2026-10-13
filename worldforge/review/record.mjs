// Record the WorldForge review's 3D clips by driving worldforge/viewer.html in headless Chrome over CDP.
//   node worldforge/review/record.mjs                    # worlds/modes from worldforge/review/round.json
//   node worldforge/review/record.mjs --worlds locator-x --modes orbit,flyin --seconds 5
//   node worldforge/review/record.mjs --resume          # same round, after an interrupted run: keep finished clips
// Writes worldforge/review/out/clips/<slug>-<mode>.mp4 (960x540, 24 fps, libx264, yuv420p) and
// worldforge/review/out/clips/index.json (which round they were recorded for; build_review.py only cuts in clips
// recorded for the current round). Needs the static server on http://127.0.0.1:8080 serving the repo root, Google
// Chrome, and the working ffmpeg in .cache/bin (or $FFMPEG).
//
// VIEWER RECORDING CONTRACT (worldforge/viewer.html implements it; this file consumes it):
//   URL  ?world=<slug>&hud=0&tour=1          hud=0 hides panels/overlays, tour=1 stops the animation loop
//   window.__wfReady === true                once the world GLB, buildings and avatars loaded (or fell back)
//   window.__wfShot(mode, t) -> true         positions the camera for t in [0,1] and renders synchronously;
//                                            mode in orbit | flyin | building | omega | council
// Frames are never faked: if the viewer lacks __wfShot, or a shot does not return true, this exits 1 with one line.
// A missing contract fails fast and is never retried: viewer.html without __wfReady/__wfShot in its source fails before
// Chrome starts, and a page that still has no window.__wfReady READY_GRACE_S (60) s after load fails once.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..', '..');
const OUT = path.join(HERE, 'out', 'clips');
const FFMPEG = process.env.FFMPEG || path.join(ROOT, '.cache', 'bin', 'ffmpeg');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE = process.env.WF_BASE || 'http://127.0.0.1:8080';
const MODES_ALL = ['orbit', 'flyin', 'building', 'omega', 'council'];
const W = 960, H = 540;

const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : dflt; };
const round = JSON.parse(fs.readFileSync(path.join(HERE, 'round.json'), 'utf8'));
const worlds = (arg('worlds') ? arg('worlds').split(',') : round.worlds) ?? ['locator-x', 'cancer-dao', 's29-metaverse-dao'];
const modes = (arg('modes') ? arg('modes').split(',') : round.modes) ?? ['flyin', 'building', 'omega', 'orbit'];
const SECONDS = Number(arg('seconds', process.env.SECONDS_PER_CLIP || 5));
const FPS = Number(process.env.FPS || 12);                  // captured frames per second; encoded at 24 fps
const N = Math.max(2, Math.round(FPS * SECONDS));
const PORT = Number(process.env.CDP_PORT || 9347);
const RESUME = process.argv.includes('--resume');         // 9333/9334 belong to tools/record.mjs and tools/snap.mjs

const fail = (msg) => { console.log(`record FAILED: ${msg}`); process.exitCode = 1; };
const bad = modes.filter((m) => !MODES_ALL.includes(m));
if (bad.length) { fail(`unknown mode(s) ${bad.join(', ')}; the contract defines ${MODES_ALL.join(', ')}`); process.exit(1); }
if (!fs.existsSync(FFMPEG)) { fail(`no ffmpeg at ${FFMPEG} (set FFMPEG)`); process.exit(1); }
for (const slug of worlds) {
  if (!fs.existsSync(path.join(ROOT, 'worldforge', 'out', slug, 'cards.json'))) { fail(`no worldforge/out/${slug}/cards.json; run node worldforge/build.mjs`); process.exit(1); }
}

// Fail fast, before Chrome starts, when the viewer is not served or does not carry the recording contract at all.
{
  const vurl = `${BASE}/worldforge/viewer.html`;
  const res = await fetch(vurl).catch((e) => e);
  if (res instanceof Error) { fail(`the static server is not reachable at ${BASE} (${res.cause?.code || res.message}); start it serving the repo root`); process.exit(1); }
  if (!res.ok) { fail(`${vurl} answered HTTP ${res.status}; the server must serve the repo root`); process.exit(1); }
  const src = await res.text();
  const missing = ['__wfReady', '__wfShot'].filter((g) => !src.includes(g));
  if (missing.length) { fail(`worldforge/viewer.html does not define window.${missing.join(' or window.')} (recording contract not implemented); no frames recorded, none faked`); process.exit(1); }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), 'wf-review-rec-'));
const recorded = [];
const problems = [];
const ATTEMPTS = Number(process.env.ATTEMPTS || 3);   // software WebGL under heavy load can lose Chrome mid-run

/** Launch headless Chrome and open a CDP session on its page; every pending call fails if the socket closes. */
async function session(n) {
  const chrome = spawn(CHROME, [
    '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${path.join(tmp, `profile${n}`)}`,
    '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl',
    '--hide-scrollbars', `--window-size=${W},${H}`, 'about:blank',
  ], { stdio: 'ignore' });
  const close = async () => { try { chrome.kill(); } catch {} await sleep(800); };
  let targets;
  for (let i = 0; i < 200 && !(targets && targets.some((t) => t.type === 'page')); i++) {
    await sleep(200);
    targets = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).catch(() => null);
  }
  if (!targets || !targets.some((t) => t.type === 'page')) { await close(); throw new Error(`Chrome did not open its debug port ${PORT} within 40 s`); }
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', () => j(new Error('CDP websocket error')), { once: true }); });
  let id = 0, lost = null; const pending = new Map();
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); const p = pending.get(m.id); if (p) { pending.delete(m.id); p.res(m); } });
  ws.addEventListener('close', () => { lost = new Error('Chrome closed the CDP connection (crashed or was killed)'); for (const p of pending.values()) p.rej(lost); pending.clear(); });
  const send = (method, params = {}, ms = 120000) => new Promise((res, rej) => {
    if (lost) return rej(lost);
    const n = ++id;
    const timer = setTimeout(() => { pending.delete(n); rej(new Error(`CDP ${method} timed out after ${ms / 1000} s`)); }, ms);
    pending.set(n, { res: (m) => { clearTimeout(timer); res(m); }, rej: (e) => { clearTimeout(timer); rej(e); } });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  const evaluate = async (expr) => {
    const m = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (m.result?.exceptionDetails) throw new Error(m.result.exceptionDetails.exception?.description?.split('\n')[0] || m.result.exceptionDetails.text);
    return m.result?.result?.value;
  };
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Page.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', { source:
    "window.__errs=[];addEventListener('error',e=>__errs.push(e.message||String(e)));addEventListener('unhandledrejection',e=>__errs.push(String(e.reason)))" });
  return { send, evaluate, close: async () => { try { ws.close(); } catch {} await close(); } };
}

class ContractMissing extends Error {}
let cleaned = false;
const READY_S = Number(process.env.READY_S || 120);       // how long a world may take to load
const GRACE_S = Number(process.env.READY_GRACE_S || 60);  // after page load, how long __wfReady may stay undefined
                                                          // (the viewer warms three.js from the CDN before its module runs)

/** Record the modes of one world that are not recorded yet, in one Chrome session. */
async function recordWorld(S, slug) {
  const url = `${BASE}/worldforge/viewer.html?world=${encodeURIComponent(slug)}&hud=0&tour=1`;
  await S.send('Page.navigate', { url });
  let st = null, loadedAt = 0;
  const t0 = Date.now();
  const errs = () => S.evaluate("JSON.stringify((window.__errs||[]).slice(0,3))").catch((e) => e.message);
  while (Date.now() - t0 < READY_S * 1000) {
    await sleep(200);
    st = await S.evaluate("({ready: window.__wfReady === true, r: typeof window.__wfReady, s: typeof window.__wfShot, doc: document.readyState})")
      .catch((e) => { if (/CDP connection/.test(e.message)) throw e; return null; });
    if (!st) continue;
    if (st.ready) break;
    if (st.doc === 'complete' && !loadedAt) loadedAt = Date.now();
    // A viewer that never defines __wfReady will never be ready: that is a missing contract, not a slow load, so it
    // fails once with one line instead of waiting out READY_S and retrying ATTEMPTS times.
    if (loadedAt && st.r === 'undefined' && Date.now() - loadedAt > GRACE_S * 1000) {
      throw new ContractMissing(`${slug}: worldforge/viewer.html never defined window.__wfReady within ${GRACE_S} s of page load` +
        ` (window.__wfShot is ${st.s}; page errors: ${await errs()}); recording contract not met, no frames recorded, none faked`);
    }
  }
  if (!st?.ready) {
    throw new Error(`${slug}: window.__wfReady ${st?.r === 'undefined' ? 'was never defined' : 'stayed false'} for ${READY_S} s (${url} | page errors: ${await errs()})`);
  }
  if (await S.evaluate('typeof window.__wfShot') !== 'function') {
    throw new ContractMissing('worldforge/viewer.html has no window.__wfShot yet (recording contract not implemented); no frames recorded, none faked');
  }
  if (!cleaned) {
    // Fresh output once the contract is confirmed: clips from an earlier round must not pass for this round's.
    // --resume (same round, after an interrupted run) keeps the clips already on disk and records only the rest.
    fs.mkdirSync(OUT, { recursive: true });
    for (const f of fs.readdirSync(OUT)) {
      const m = f.match(/^(.+)-(orbit|flyin|building|omega|council)\.mp4$/);
      if (RESUME && m && worlds.includes(m[1]) && modes.includes(m[2])) {
        recorded.push({ slug: m[1], mode: m[2], file: path.relative(ROOT, path.join(OUT, f)), frames: N, captured_fps: FPS, seconds: Number((N / FPS).toFixed(3)) });
        console.log(`  ${f}: kept (--resume)`);
      } else if (f.endsWith('.mp4') || f === 'index.json') fs.rmSync(path.join(OUT, f));
    }
    cleaned = true;
  }
  for (const mode of modes) {
    if (recorded.some((c) => c.slug === slug && c.mode === mode)) continue;
    const dir = path.join(tmp, `${slug}-${mode}`);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    let small = 0;
    for (let k = 0; k < N; k++) {
      const t = (k / (N - 1)).toFixed(5);
      let ok;
      try { ok = await S.evaluate(`window.__wfShot(${JSON.stringify(mode)}, ${t})`); }
      catch (e) { throw new Error(`${slug}: __wfShot('${mode}', ${t}) failed: ${e.message}`); }
      if (ok !== true) throw new Error(`${slug}: __wfShot('${mode}', ${t}) returned ${JSON.stringify(ok)}, not true`);
      const shot = await S.send('Page.captureScreenshot', { format: 'jpeg', quality: 85 });
      const buf = Buffer.from(shot.result.data, 'base64');
      if (buf.length < 9000) small++;
      fs.writeFileSync(path.join(dir, `f${String(k).padStart(4, '0')}.jpg`), buf);
    }
    const file = path.join(OUT, `${slug}-${mode}.mp4`);
    execFileSync(FFMPEG, ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(dir, 'f%04d.jpg'),
      '-vf', `scale=${W}:${H}:out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,fps=24`, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p',
      '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-movflags', '+faststart', file]);
    fs.rmSync(dir, { recursive: true, force: true });
    if (small > N / 2) problems.push(`${slug}-${mode}: ${small}/${N} frames under 9 KB (may be blank)`);
    recorded.push({ slug, mode, file: path.relative(ROOT, file), frames: N, captured_fps: FPS, seconds: Number((N / FPS).toFixed(3)) });
    console.log(`  ${slug}-${mode}.mp4: ${N} frames`);
  }
}

let S = null, launches = 0;
try {
  for (const slug of worlds) {
    for (let attempt = 1; ; attempt++) {
      try {
        if (!S) S = await session(++launches);
        await recordWorld(S, slug);
        break;
      } catch (e) {
        if (e instanceof ContractMissing || attempt >= ATTEMPTS) throw e;
        console.log(`  retry ${slug} (attempt ${attempt + 1}/${ATTEMPTS}): ${e.message}`);
        if (S) { await S.close(); S = null; }
      }
    }
  }
} catch (e) {
  fail(e.message);
} finally {
  if (S) await S.close();
  try { fs.rmSync(tmp, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); } catch {}
}

const want = worlds.length * modes.length;
if (recorded.length) {
  // Ordered as round.json lists worlds and modes. No timestamps: the round number says which review these belong to.
  recorded.sort((a, b) => worlds.indexOf(a.slug) - worlds.indexOf(b.slug) || modes.indexOf(a.mode) - modes.indexOf(b.mode));
  fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify({
    schemaVersion: 'worldforge-review-clips/0.1', round: round.n, worlds, modes, complete: recorded.length === want,
    recorder: 'headless Chrome (software WebGL, swiftshader) driving worldforge/viewer.html via window.__wfShot',
    problems, clips: recorded,
  }, null, 1) + '\n');
}
if (!process.exitCode) {
  console.log(`recorded ${recorded.length}/${want} clips (${worlds.length} worlds x ${modes.length} modes, ${N} frames each)${launches > 1 ? `, ${launches} Chrome launches` : ''} -> worldforge/review/out/clips${problems.length ? ` | warnings: ${problems.join('; ')}` : ''}`);
}
