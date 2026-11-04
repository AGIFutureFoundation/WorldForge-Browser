// ps2_hist.mjs -- objective luminance check for the PS2 look: draws the WebGL canvas into a 2D
// canvas and reports an 8-bin luminance histogram plus top-half (sky+buildings) vs bottom-half
// (ground) means, in PS2 mode and ?modern=1. Guards against "everything crushed to black" or
// "ground blown to white" regressions the eye (or a vision model) can only guess at.
// Usage: node earth/ps2_hist.mjs <slug>
import { session, open, sleep } from './cdp.mjs';

const arg = process.argv[2] || 's12-parking-smart-x';
const S = await session(1024, 640);
const SAMPLE = `(function(){ const c = document.getElementById('c'); if (!c) return 'no canvas';
  const t = document.createElement('canvas'); t.width = c.width; t.height = c.height;
  t.getContext('2d').drawImage(c, 0, 0);
  const d = t.getContext('2d').getImageData(0, 0, t.width, t.height).data;
  const bins = new Array(8).fill(0); let sum = 0, n = 0, top = 0, tn = 0, bot = 0, bn = 0;
  const half = t.height / 2;
  for (let y = 0; y < t.height; y++) for (let x = 0; x < t.width; x++) {
    const i = (y * t.width + x) * 4, l = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
    bins[Math.min(7, l / 32 | 0)]++; sum += l; n++;
    if (y < half) { top += l; tn++; } else { bot += l; bn++; } }
  const px = v => (100 * v / n).toFixed(1) + '%';
  return JSON.stringify({ size: t.width + 'x' + t.height, meanL: (sum / n).toFixed(1),
    topMeanL: (top / tn).toFixed(1), botMeanL: (bot / bn).toFixed(1),
    hist: bins.map(px) }); })()`;

try {
  for (const [name, extra] of [['ps2', ''], ['modern', '&modern=1']]) {
    await open(S, arg, extra);
    await sleep(3500);
    const r = JSON.parse(await S.ev(SAMPLE));
    console.log(`${name}: size=${r.size} meanL=${r.meanL} top(sky+bldg)=${r.topMeanL} bot(ground)=${r.botMeanL}`);
    console.log(`       hist(0-31..224-255): ${r.hist.join(' ')}`);
  }
} catch (e) { console.log('FAIL ' + e.message); if (S.logs.length) console.log('  js errors: ' + S.logs.join(' | ')); }
finally { S.close(); }
