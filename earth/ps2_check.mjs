// ps2_check.mjs -- verify the PS2 pass: open a world in default (PS2) and ?modern=1 modes,
// confirm the CRT overlay + pixelated upscale only appear in PS2 mode, save screenshots.
// Usage: node earth/ps2_check.mjs [slug] [outdir]   (needs earth/serve.mjs on :8094)
import fs from 'node:fs';
import { session, open, sleep } from './cdp.mjs';

const slug = process.argv[2] || 'climate-dao';
const out = process.argv[3] || '/tmp/ps2';
fs.mkdirSync(out, { recursive: true });

let bad = 0;
const S = await session(1024, 640);
try {
  for (const [name, extra, wantCRT] of [['ps2', '', true], ['modern', '&modern=1', false]]) {
    S.logs.length = 0;
    await open(S, slug, extra);
    await sleep(3500);
    const state = JSON.parse(await S.ev(`JSON.stringify({crt: !!document.getElementById('ps2-crt'),
      img: document.getElementById('c').style.imageRendering || '', ready: !!(window.__wf||{}).ready})`));
    const ok = state.ready && state.crt === wantCRT && (wantCRT ? state.img === 'pixelated' : true);
    const shot = await S.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    fs.writeFileSync(`${out}/${slug}-${name}.png`, Buffer.from(shot.result?.data ?? shot.data, 'base64'));
    console.log(`${name}: ready=${state.ready} crt=${state.crt} pixelated=${state.img} ${ok ? 'OK' : 'MISMATCH'}`
      + ` -> ${out}/${slug}-${name}.png` + (S.logs.length ? ' | js errors: ' + S.logs.join(' | ') : ''));
    if (!ok || S.logs.length) bad++;
  }
} catch (e) { console.log('FAIL ' + e.message); if (S.logs.length) console.log('  js errors: ' + S.logs.join(' | ')); bad++; }
finally { S.close(); }
process.exit(bad ? 1 : 0);
