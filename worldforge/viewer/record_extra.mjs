// Extra recordings and a live check for worldforge/viewer.html, using the same CDP pattern as worldforge/review/record.mjs.
// record.mjs only knows orbit | flyin | building | omega | council; this records the modes it does not know (landmark),
// renders 1280x720 still candidates for any mode, and checks the viewer live in headless Chrome.
//   node worldforge/viewer/record_extra.mjs clips  [--worlds a,b] [--modes landmark] [--seconds 5]
//        -> worldforge/review/out/clips/<slug>-<mode>.mp4 (960x540, 24 fps, same encode as record.mjs) and
//           worldforge/review/out/clips/index.extra.json (kept out of index.json, which build_review.py reads as the
//           round's clip list; record.mjs rewrites index.json and deletes every clip when it starts without --resume)
//   node worldforge/viewer/record_extra.mjs stills --world locator-x --modes flyin,landmark --ts 0.4,0.8 --dir <dir>
//        -> <dir>/<slug>-<mode>-<t>.jpg at 1280x720 (candidates; pick and copy the best by hand after looking)
//   node worldforge/viewer/record_extra.mjs snap --world <slug> [--q '&card=<id>'] [--js <expr>] --out f.jpg   (HUD screenshot)
//   node worldforge/viewer/record_extra.mjs verify [--worlds a,b]
//        -> one line per world and a final "LIVE OK" / "LIVE FAIL" line: advisors, coordinator and landmark placed with
//           their GLBs, advisor cards selectable and framed, coordinator intro plays its HEAD-checked recording or says why not.
// Needs the static server on http://127.0.0.1:8080 serving the repo root, Google Chrome, and .cache/bin/ffmpeg for clips.
// Frames are never faked: a shot that does not return true stops the run.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..', '..');
const CLIPS = path.join(ROOT, 'worldforge', 'review', 'out', 'clips');
const FFMPEG = process.env.FFMPEG || path.join(ROOT, '.cache', 'bin', 'ffmpeg');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE = process.env.WF_BASE || 'http://127.0.0.1:8080';
const PORT = Number(process.env.CDP_PORT || 9351);      // 9333/9334 tools/*, 9347 review/record.mjs
const cmd = process.argv[2];
const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i > 0 ? process.argv[i + 1] : d; };
const WORLDS = (arg('worlds') ?? arg('world') ?? 'locator-x,cancer-dao,s29-metaverse-dao').split(',');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), 'wf-extra-'));

async function session(W, H) {
  const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${path.join(tmp, 'profile')}`,
    '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl',
    '--autoplay-policy=no-user-gesture-required', '--mute-audio', '--hide-scrollbars', `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
  let targets;
  for (let i = 0; i < 200 && !(targets && targets.some((t) => t.type === 'page')); i++) { await sleep(200); targets = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).catch(() => null); }
  if (!targets) { chrome.kill(); throw new Error(`Chrome did not open port ${PORT}`); }
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
  let id = 0; const pending = new Map();
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); const p = pending.get(m.id); if (p) { pending.delete(m.id); p(m); } });
  const send = (method, params = {}) => new Promise((res, rej) => { const n = ++id; const tm = setTimeout(() => rej(new Error(`${method} timed out`)), 180000); pending.set(n, (m) => { clearTimeout(tm); res(m); }); ws.send(JSON.stringify({ id: n, method, params })); });
  const evaluate = async (expression) => { const m = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (m.result?.exceptionDetails) throw new Error(m.result.exceptionDetails.exception?.description?.split('\n')[0] ?? 'eval failed'); return m.result?.result?.value; };
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Page.enable');
  return { send, evaluate, close: async () => { try { ws.close(); } catch {} chrome.kill(); await sleep(600); } };
}
async function open(S, slug, extra = '') {
  await S.send('Page.navigate', { url: `${BASE}/worldforge/viewer.html?world=${encodeURIComponent(slug)}${extra}` });
  const t0 = Date.now();
  while (Date.now() - t0 < 150000) { await sleep(300); const r = await S.evaluate('window.__wfReady === true && window.__wfInfo?.().world').catch(() => null); if (r === slug) return; }
  throw new Error(`${slug}: window.__wfReady not true within 150 s`);
}
async function shoot(S, mode, t, q = 88) {
  const ok = await S.evaluate(`window.__wfShot(${JSON.stringify(mode)}, ${t})`);
  if (ok !== true) throw new Error(`__wfShot('${mode}', ${t}) returned ${JSON.stringify(ok)}`);
  return Buffer.from((await S.send('Page.captureScreenshot', { format: 'jpeg', quality: q })).result.data, 'base64');
}

let S = null;
try {
  if (cmd === 'clips') {
    const modes = arg('modes', 'landmark').split(','), FPS = Number(process.env.FPS || 12), N = Math.max(2, Math.round(FPS * Number(arg('seconds', 5))));
    const W = 960, H = 540; S = await session(W, H);
    const idxFile = path.join(CLIPS, 'index.extra.json');
    const prev = fs.existsSync(idxFile) ? JSON.parse(fs.readFileSync(idxFile, 'utf8')).clips ?? [] : [];
    const done = [];
    fs.mkdirSync(CLIPS, { recursive: true });
    for (const slug of WORLDS) {
      await open(S, slug, '&hud=0&tour=1');
      for (const mode of modes) {
        const dir = path.join(tmp, `${slug}-${mode}`); fs.mkdirSync(dir, { recursive: true });
        for (let k = 0; k < N; k++) fs.writeFileSync(path.join(dir, `f${String(k).padStart(4, '0')}.jpg`), await shoot(S, mode, (k / (N - 1)).toFixed(5), 85));
        const file = path.join(CLIPS, `${slug}-${mode}.mp4`);
        execFileSync(FFMPEG, ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(dir, 'f%04d.jpg'),
          '-vf', `scale=${W}:${H}:out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,fps=24`, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p',
          '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', file]);
        done.push({ slug, mode, file: path.relative(ROOT, file), frames: N, captured_fps: FPS, seconds: Number((N / FPS).toFixed(3)) });
        console.log(`  ${slug}-${mode}.mp4: ${N} frames`);
      }
    }
    const keep = prev.filter((c) => !done.some((d) => d.slug === c.slug && d.mode === c.mode) && fs.existsSync(path.join(ROOT, c.file)));
    fs.writeFileSync(idxFile, JSON.stringify({ schemaVersion: 'worldforge-review-clips-extra/0.1',
      note: 'clips in modes worldforge/review/record.mjs does not record; deliberately not in index.json, so build_review.py does not cut them in unless the lead adds them',
      recorder: 'headless Chrome (software WebGL, swiftshader) driving worldforge/viewer.html via window.__wfShot (worldforge/viewer/record_extra.mjs)',
      clips: [...keep, ...done] }, null, 1) + '\n');
    console.log(`recorded ${done.length} extra clips -> worldforge/review/out/clips (index.extra.json)`);
  } else if (cmd === 'stills') {
    const [W, H] = arg('size', '1280x720').split('x').map(Number), dir = arg('dir', path.join(tmp, 'stills'));
    const modes = arg('modes', 'flyin,building,omega,orbit,council,landmark').split(','), ts = arg('ts', '0.5,0.8,1').split(',');
    fs.mkdirSync(dir, { recursive: true }); S = await session(W, H);
    for (const slug of WORLDS) {
      await open(S, slug, '&hud=0&tour=1');
      for (const mode of modes) for (const t of ts) { const f = path.join(dir, `${slug}-${mode}-${t}.jpg`); fs.writeFileSync(f, await shoot(S, mode, t, 92)); console.log(f); }
    }
  } else if (cmd === 'verify') {
    S = await session(1440, 900);
    const fails = [];
    for (const slug of WORLDS) {
      await open(S, slug);
      const cards = JSON.parse(fs.readFileSync(path.join(ROOT, 'worldforge', 'out', slug, 'cards.json'), 'utf8')).cards;
      const info = await S.evaluate('window.__wfInfo()');
      const want = cards.filter((c) => ['agent', 'omega', 'coordinator', 'advisor'].includes(c.kind));
      const got = new Map(info.avatars.map((a) => [a.card, a]));
      const lacking = want.filter((c) => !got.has(c.cardId)).map((c) => c.cardId);
      const noModel = want.filter((c) => got.has(c.cardId) && !got.get(c.cardId).model).map((c) => c.cardId);
      if (lacking.length) fails.push(`${slug}: no avatar for ${lacking.join(', ')}`);
      if (noModel.length) fails.push(`${slug}: stand-in instead of GLB for ${noModel.join(', ')}`);
      for (const c of want) { const a = got.get(c.cardId); if (a && c.volum && (Math.abs(a.at[0] - c.volum.center[0]) > 0.01 || Math.abs(a.at[2] - c.volum.center[2]) > 0.01) && Math.hypot(c.volum.center[0], c.volum.center[2]) >= 4) fails.push(`${c.cardId}: placed at ${a.at} not card centre ${c.volum.center}`); }
      if (!info.landmark?.model) fails.push(`${slug}: landmark not loaded`);
      // select each advisor and the coordinator through the card list; the camera must move and the panel must offer Frame
      const sel = [];
      for (const c of want.filter((x) => x.kind === 'advisor' || x.kind === 'coordinator')) {
        const r = await S.evaluate(`(async () => { const before = __wfCam().pos.join(); const b = [...document.querySelectorAll('#cardlist button')].find((x) => x.dataset.id === ${JSON.stringify(c.cardId)});
          if (!b) return { err: 'not in card list' }; b.click(); await new Promise((r) => setTimeout(r, 50));
          return { moved: __wfCam().pos.join() !== before, selected: __wfCam().selected, frame: !!document.querySelector('#dFrame'), walk: !!document.querySelector('#dWalk'),
            avatarRow: [...document.querySelectorAll('#detail th')].find((t) => t.textContent === 'Avatar')?.nextElementSibling?.textContent ?? '', intro: document.querySelector('#detail .line p')?.textContent ?? '' }; })()`);
        if (r.err || r.selected !== c.cardId || !r.frame || !r.walk || !/model loaded/.test(r.avatarRow) || !r.intro) fails.push(`${c.cardId}: select ${JSON.stringify(r)}`);
        sel.push(c.cardId.split('/').pop().split(':')[0]);
      }
      // intro speech for the coordinator, one advisor and the Omega: the row's recording if the server has it, the Omega's
      // hive greet line next, else the labelled browser voice
      const rows = JSON.parse(fs.readFileSync(path.join(ROOT, 'worldforge', 'out', 'avatars', 'index.json'), 'utf8')).rows.filter((r) => r.world === slug);
      const voiced = [];
      for (const c of [cards.find((x) => x.kind === 'coordinator'), cards.find((x) => x.kind === 'advisor'), cards.find((x) => x.kind === 'omega')]) {
        const row = rows.find((r) => r.cardId === c.cardId) ?? {};
        const cands = [row.audio, c.kind === 'omega' ? row.voice?.audio?.greet ?? c.voice?.lines?.find((l) => l.id === 'greet')?.audio : null].filter(Boolean);
        const expect = cands.find((p) => fs.existsSync(path.join(ROOT, p))) ?? null;
        const sp = await S.evaluate(`(async () => { [...document.querySelectorAll('#cardlist button')].find((x) => x.dataset.id === ${JSON.stringify(c.cardId)}).click(); await new Promise((r) => setTimeout(r, 400));
          const rec = document.querySelector('#rec-intro')?.textContent; window.__wfVoice = null; document.querySelector('#detail .speak[data-intro]').click();
          for (let i = 0; i < 40 && !window.__wfVoice; i++) await new Promise((r) => setTimeout(r, 100));
          return { rec, voice: window.__wfVoice, vl: document.querySelector('#vl-intro')?.textContent }; })()`);
        if (expect && !(sp.voice?.src ?? '').endsWith(expect)) fails.push(`${c.cardId}: ${expect} exists but was not played (${JSON.stringify(sp)})`);
        if (!expect && !/not voiced yet|no recording path/.test(sp.vl ?? '')) fails.push(`${c.cardId}: no recording, but the label says ${sp.vl}`);
        if (row.audio && /present/.test(sp.rec ?? '') !== fs.existsSync(path.join(ROOT, row.audio))) fails.push(`${c.cardId}: panel says "${sp.rec}" for ${row.audio}`);
        voiced.push(`${c.kind}=${sp.voice?.src ? sp.voice.src.split('/').slice(-3).join('/') : 'browser'}`);
      }
      // landmark selectable
      const lm = await S.evaluate(`(async () => { [...document.querySelectorAll('#cardlist button')].find((x) => x.dataset.id === 'landmark:${slug}')?.click(); await new Promise((r) => setTimeout(r, 50));
        return { selected: __wfCam().selected, text: document.querySelector('#detail').textContent.includes('synthetic civic landmark, not a real building') }; })()`);
      if (lm.selected !== `landmark:${slug}` || !lm.text) fails.push(`${slug}: landmark select ${JSON.stringify(lm)}`);
      // every shot mode returns true
      for (const m of ['flyin', 'building', 'omega', 'orbit', 'council', 'landmark']) if (await S.evaluate(`window.__wfShot('${m}', 0.5)`) !== true) fails.push(`${slug}: __wfShot('${m}') not true`);
      const errs = await S.evaluate('(window.__errs || []).slice(0, 3)');
      if (errs.length) fails.push(`${slug}: page errors ${JSON.stringify(errs)}`);
      console.log(`  ${slug}: ${info.avatars.length} avatars (${info.stats.avatars} models; ${JSON.stringify(info.stats.avatarKinds)}), landmark ${info.landmark?.style} ${info.landmark?.height} m at ${info.landmark?.at} yaw ${info.landmark?.yawDeg}, selected ${sel.join('/')}, voices ${voiced.join(', ')}`);
    }
    if (fails.length) { for (const f of fails.slice(0, 20)) console.log(`  ${f}`); console.log(`LIVE FAIL: ${fails.length} problems`); process.exitCode = 1; }
    else console.log(`LIVE OK: ${WORLDS.length} worlds, every agent/omega/coordinator/advisor card has its GLB avatar, landmark loaded and selectable, 6 shot modes, HEAD-checked intro audio`);
  } else if (cmd === 'snap') {
    // node worldforge/viewer/record_extra.mjs snap --world <slug> --q '&card=<id>' --js '<expr run before the shot>' --out f.jpg
    const [W, H] = arg('size', '1440x900').split('x').map(Number); S = await session(W, H);
    await open(S, WORLDS[0], arg('q', '')); await sleep(800);
    if (arg('js')) await S.evaluate(arg('js'));
    await sleep(400);
    fs.writeFileSync(arg('out', path.join(tmp, 'snap.jpg')), Buffer.from((await S.send('Page.captureScreenshot', { format: 'jpeg', quality: 88 })).result.data, 'base64'));
    console.log(arg('out'));
  } else { console.log('usage: record_extra.mjs clips|stills|verify [--worlds a,b] [--modes m] [--ts t1,t2] [--dir d]'); process.exitCode = 2; }
} catch (e) { console.log(`record_extra FAILED: ${e.message}`); process.exitCode = 1; }
finally { if (S) await S.close(); try { fs.rmSync(path.join(tmp, 'profile'), { recursive: true, force: true }); } catch {} }
