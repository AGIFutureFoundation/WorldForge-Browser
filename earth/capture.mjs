// Capture WorldForge Earth worlds in headless Chrome.
//   node earth/capture.mjs verify --worlds a,b                    -> live check (loads, counts, robot episodes, console errors)
//   node earth/capture.mjs stills --worlds a,b --dir d            -> d/<slug>.jpg, d/<slug>-hud.jpg, d/<slug>-court.jpg
//   node earth/capture.mjs video  --worlds a,b --out f.mp4 [--seconds 6]   -> walkthrough film (guided tour per world)
// Needs site/ served at WF_BASE (default http://127.0.0.1:8094), Google Chrome, ffmpeg on PATH.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs'; import path from 'node:path';
import { session, open, shot, hud, wf, sleep, tmp } from './cdp.mjs';

const cmd = process.argv[2];
const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i > 0 ? process.argv[i + 1] : d; };
const WORLDS = arg('worlds', 'climate-dao').split(',');
let S;
try {
  if (cmd === 'verify') {
    S = await session(1440, 900); let fail = 0;
    for (const slug of WORLDS) {
      try {
        const w = await open(S, slug); await sleep(20000);
        const rec = await S.ev('window.__wf.records()');
        console.log(`OK   ${slug.padEnd(30)} ${JSON.stringify(w.counts)} robotEpisodes=${rec} consoleErrors=${S.logs.length}`);
        if (S.logs.length) console.log('     ', S.logs.slice(0, 3).join(' | '));
      } catch (e) { fail++; console.log(`FAIL ${slug}: ${e.message}`); }
    }
    console.log(fail ? `LIVE FAIL ${fail}` : 'LIVE OK');
  } else if (cmd === 'stills') {
    const dir = arg('dir', 'stills'); fs.mkdirSync(dir, { recursive: true }); S = await session(1280, 720);
    for (const slug of WORLDS) {
      try {
        await open(S, slug); await sleep(3000);
        await wf(S, 'w.fly(w.stops[0], 150)'); await sleep(3200);
        await hud(S, false); fs.writeFileSync(path.join(dir, `${slug}.jpg`), await shot(S));
        await hud(S, true); fs.writeFileSync(path.join(dir, `${slug}-hud.jpg`), await shot(S, 80));
        await wf(S, 'w.fly(w.stops[1], 24); setTimeout(() => w.shoot(), 2600)'); await sleep(3300);
        await hud(S, false); fs.writeFileSync(path.join(dir, `${slug}-court.jpg`), await shot(S));
        console.log('still', slug);
      } catch (e) { console.log('skip', slug, e.message); }
    }
  } else if (cmd === 'video') {
    const out = arg('out', 'walkthrough.mp4'), secs = Number(arg('seconds', 6)), FPS = 8;
    S = await session(960, 540); const dir = path.join(tmp, 'f'); fs.mkdirSync(dir); let k = 0;
    for (const slug of WORLDS) {
      try {
        await open(S, slug, '&tour=1'); await sleep(2000);
        await S.ev(`(()=>{document.querySelectorAll('.panel').forEach(p=>p.style.display='none');const d=document.createElement('div');d.textContent=document.getElementById('title').textContent+' - '+document.getElementById('place').textContent;d.style.cssText='position:fixed;left:24px;bottom:40px;font:600 24px system-ui;color:#fff;text-shadow:0 2px 8px #000;z-index:9';document.body.appendChild(d)})()`);
        for (let i = 0; i < secs * FPS; i++) { fs.writeFileSync(path.join(dir, `f${String(k++).padStart(5, '0')}.jpg`), await shot(S, 82)); await sleep(1000 / FPS); }
        console.log('filmed', slug);
      } catch (e) { console.log('skip', slug, e.message); }
    }
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(dir, 'f%05d.jpg'),
      '-vf', 'fps=24,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26', '-movflags', '+faststart', out]);
    console.log('video', out, `${k} frames`);
  }
} finally { S?.close(); }
