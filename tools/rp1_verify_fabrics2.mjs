// rp1_verify_fabrics2.mjs -- verify fabric home pages by clicking each company's FABRIC nav item.
// Log: /tmp/rp1-verify2.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-verify2.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `verify2, ${new Date().toISOString()}\n`);

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('dev.rp1.com'));
if (!page) { log('FATAL no dev tab'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Page.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const COMPANIES = [
  ['SmartCiti', 137, 'SmartCiti.X'],
  ['Cognition', 131, 'Cognition.X'],
  ['Diagnostic', 133, 'Diagnostic.X'],
  ['Empathic', 132, 'Empathic.X'],
];

for (const [name, cid, fabricNav] of COMPANIES) {
  await send('Page.navigate', { url: `https://dev.rp1.com/company/${cid}/home` });
  await sleep(3000);
  await ev(`(() => {
    const els = [...document.querySelectorAll('span, a, li, div, button')].filter(el => (el.innerText || '').trim() === ${JSON.stringify(fabricNav)} && el.children.length === 0);
    if (els.length) { els[els.length - 1].click(); }
    return els.length;
  })()`);
  await sleep(3500);
  const st = await ev(`(() => {
    const inputs = [...document.querySelectorAll('input')].map(i => ({ n: (i.name || i.placeholder || i.id || '').slice(0, 60), v: (i.value || '').slice(0, 110) }))
      .filter(x => x.v && (x.v.includes('worldforge') || x.v.includes('enter.rp1') || /lat|lon/i.test(x.n)));
    const txt = (document.body.innerText || '');
    const lat = /Latitude\\s*\\n\\s*([\\-0-9.]+)/.exec(txt);
    const lon = /Longitude\\s*\\n\\s*([\\-0-9.]+)/.exec(txt);
    return JSON.stringify({ url: location.href, fields: inputs, lat: lat ? lat[1] : null, lon: lon ? lon[1] : null }, null, 1);
  })()`);
  log(`${name} (${cid}): ${st}`);
}
log('--- verify2 done');
ws.close();
process.exit(0);
