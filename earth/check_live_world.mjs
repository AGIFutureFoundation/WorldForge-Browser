// check_live_world.mjs -- open LIVE world pages and report readiness, counts and renderer errors.
// Usage: WF_BASE=https://agifuturefoundation.github.io/WorldForge-Browser CDP_PORT=9362 \
//        node earth/check_live_world.mjs chi-pilsen [more,slugs...]
import { session, open, sleep } from './cdp.mjs';

const slugs = process.argv.slice(2);
if (!slugs.length) { console.error('usage: check_live_world.mjs slug [slug...]'); process.exit(2); }

let bad = 0;
const S = await session(1280, 720);
try {
  for (const slug of slugs) {
    process.stdout.write(slug + ' ... ');
    S.logs.length = 0;
    try {
      await open(S, slug, '', { timeoutMs: 90000 });
      await sleep(4000);
      const r = await S.ev('(function(){const w=window.__wf||{};return JSON.stringify({ready:!!w.ready,slug:w.slug,counts:w.counts||null});})()');
      console.log(r);
      if (S.logs.length) { console.log('  js errors:', S.logs.slice(0, 3).join(' | ')); bad++; }
    } catch (e) {
      console.log('FAIL ' + e.message);
      if (S.logs.length) console.log('  js errors:', S.logs.slice(0, 3).join(' | '));
      bad++;
    }
  }
} finally { S.close(); }
process.exit(bad ? 1 : 0);
