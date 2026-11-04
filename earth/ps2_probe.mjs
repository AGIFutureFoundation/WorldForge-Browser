// ps2_probe.mjs -- prove the PS2 pass numerically: internal render resolution, Lambert swap +
// texture-page budget stats from window.__wf.ps2, and a 4s rAF frame-time sample (avg fps, p95,
// worst frame ms). SwiftShader software WebGL: fps is a regression signal, not a GPU number.
// Usage: node earth/ps2_probe.mjs <slug>        -- a world, PS2 mode then ?modern=1
//        node earth/ps2_probe.mjs page:<path>   -- any page (e.g. page:/earth/ar-training.html), PS2 mode only
import { session, open, sleep, BASE } from './cdp.mjs';

const arg = process.argv[2] || 'climate-dao';
const isPage = arg.startsWith('page:');
const S = await session(1024, 640);
const FPS = `(function(){ return new Promise(res => {
  const t = []; let last = performance.now();
  function f(now) { t.push(now - last); last = now; if (now - t0 < 4000) requestAnimationFrame(f);
    else { t.sort((a,b)=>a-b); const p = q => t[Math.min(t.length - 1, Math.floor(q * t.length))];
      res(JSON.stringify({ frames: t.length, avgFps: +(1000 / (t.reduce((a,b)=>a+b,0) / t.length)).toFixed(1),
        p95ms: +p(.95).toFixed(1), worstMs: +t[t.length-1].toFixed(1) })); } }
  const t0 = performance.now(); requestAnimationFrame(f); }); })()`;

try {
  const modes = isPage ? [['ps2', arg.slice(5), false]] : [['ps2', `?world=${arg}`, false], ['modern', `?world=${arg}&modern=1`, true]];
  for (const [name, target] of modes) {
    if (isPage) await S.send('Page.navigate', { url: BASE + target });
    else await open(S, arg, name === 'modern' ? '&modern=1' : '');
    await sleep(3500);
    const c = JSON.parse(await S.ev(`(function(){ const c = document.getElementById('c');
      return JSON.stringify({ buf: c ? c.width + 'x' + c.height : '', css: c ? c.clientWidth + 'x' + c.clientHeight : '',
        ps2: (window.__wf || {}).ps2 || null, ready: !!(window.__wf || {}).ready }); })()`));
    const fps = JSON.parse(await S.ev(FPS).catch(() => 'null'));
    console.log(`${name}: buffer=${c.buf || 'n/a'} css=${c.css || 'n/a'} ready=${c.ready}`
      + (c.ps2 ? ` lambertSwaps=${c.ps2.materials} mapsDownscaled=${c.ps2.mapsDownscaled} texMP ${c.ps2.mpBefore}->${c.ps2.mpAfter}` : '')
      + (fps ? ` fps=${fps.avgFps}(${fps.frames}f) p95=${fps.p95ms}ms worst=${fps.worstMs}ms` : '')
      + (S.logs.length ? ' | js errors: ' + S.logs.join(' | ') : ''));
  }
} catch (e) { console.log('FAIL ' + e.message); if (S.logs.length) console.log('  js errors: ' + S.logs.join(' | ')); }
finally { S.close(); }
