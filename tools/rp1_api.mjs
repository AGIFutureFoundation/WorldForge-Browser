// rp1_api.mjs -- find the Dev Center's data API: capture XHR/fetch on /home, replay the promising
// ones in-page (auth cookies included), dump company data with ids to /tmp/rp1-companies.txt.
import fs from 'node:fs';

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { fs.writeFileSync('/tmp/rp1-companies.txt', 'no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const apiReqs = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.includes('dev.rp1.com') && !/\.(js|css|png|jpg|svg|woff|ico|map)/.test(u)) apiReqs.push(u);
  }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');

await send('Page.navigate', { url: 'https://dev.rp1.com/home' });
await new Promise(r => setTimeout(r, 4000));

// replay every captured dev.rp1.com endpoint in-page and look for company arrays
const out = [];
out.push('--- captured endpoints ---');
out.push(...apiReqs.slice(0, 40));
const probe = await ev(`(async () => {
  const urls = ${JSON.stringify(apiReqs.slice(0, 40))};
  const results = [];
  for (const u of urls) {
    try {
      const r = await fetch(u, { credentials: 'include' });
      const ct = r.headers.get('content-type') || '';
      if (!ct.includes('json')) continue;
      const j = await r.json();
      const s = JSON.stringify(j);
      if (s.length > 500000) { results.push({ u, len: s.length, hint: 'large' }); continue; }
      // look for company-ish arrays
      const arrs = [];
      const walk = (o, path) => {
        if (Array.isArray(o) && o.length > 2 && o[0] && typeof o[0] === 'object' && ('id' in o[0] || 'name' in o[0] || 'Name' in o[0])) arrs.push(path);
        else if (o && typeof o === 'object') for (const k of Object.keys(o)) walk(o[k], path + '.' + k);
      };
      walk(j, '');
      results.push({ u, arrays: arrs.slice(0, 6), sample: s.slice(0, 300) });
    } catch (e) { results.push({ u, err: String(e).slice(0, 60) }); }
  }
  return JSON.stringify(results, null, 1);
})()`);
out.push('--- endpoint probes ---');
out.push(probe || '(none)');
fs.writeFileSync('/tmp/rp1-companies.txt', out.join('\n'));
console.log('written /tmp/rp1-companies.txt');
ws.close();
process.exit(0);
