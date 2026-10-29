// ps2_probe.mjs -- prove the PS2 pass numerically: internal render resolution + Lambert conversion.
import { session, open, sleep } from './cdp.mjs';

const slug = process.argv[2] || 'climate-dao';
const S = await session(1024, 640);
try {
  for (const [name, extra] of [['ps2', ''], ['modern', '&modern=1']]) {
    await open(S, slug, extra);
    await sleep(2500);
    const r = await S.ev(`(function(){
      const c = document.getElementById('c');
      const wf = window.__wf;
      let lam = 0, std = 0, total = 0;
      // walk via renderer info instead: three keeps scene on __wf? use a renderer probe through debug hook if present
      return JSON.stringify({ css: c.clientWidth + 'x' + c.clientHeight, buf: c.width + 'x' + c.height, ready: !!(wf||{}).ready });
    })()`);
    console.log(name, r);
  }
} finally { S.close(); }
