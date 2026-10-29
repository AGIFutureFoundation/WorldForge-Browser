// rp1_wizard.mjs -- run the SmartCiti "Attach Fabric" wizard with worldforge-api.fly.dev as the
// metaverse server; capture every request RP1 makes to our server so we can serve what it wants.
// Log: /tmp/rp1-wizard.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-wizard.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `wizard, ${new Date().toISOString()}\n`);
const SERVER_URL = process.argv[2] || 'https://worldforge-api.fly.dev/fabric/73/1/';

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { log('FATAL no tab'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const reqs = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.startsWith('data:')) return;
    reqs.push(`${m.params.request.method} ${u.slice(0, 140)}`);
  }
  if (m.method === 'Network.responseReceived' && m.params.response.url.includes('worldforge')) {
    reqs.push(`  <- ${m.params.response.status} ${m.params.response.url.slice(0, 120)}`);
  }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

await send('Page.navigate', { url: 'https://dev.rp1.com/company/137/fabric/create' });
await sleep(3000);
const fill = await ev(`(() => {
  const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('YOURMVSERVERURL') || (i.placeholder || '').toLowerCase().includes('spatial fabric'));
  if (!inp) return 'NO_INPUT (inputs: ' + [...document.querySelectorAll('input')].map(i => i.placeholder).filter(Boolean).slice(0,5).join(',') + ')';
  inp.focus(); inp.value = ${JSON.stringify(SERVER_URL)};
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true }));
  return 'FILLED';
})()`);
log(`fill: ${fill}`);
const clicked = await ev(`(() => {
  const b = [...document.querySelectorAll('button')].filter(x => (x.offsetParent || x.getClientRects().length) && (x.innerText || '').trim() === 'Continue');
  if (!b.length) return 'NO_CONTINUE';
  b[0].click(); return 'CLICKED';
})()`);
log(`continue: ${clicked}`);
await sleep(10000);
log('--- requests to our server + api ---');
log(reqs.filter(r => r.includes('worldforge') || r.startsWith('  <-')).join('\n') || '(none)');
log('--- other requests (last 15) ---');
log(reqs.slice(-15).join('\n'));
const state = await ev(`(() => JSON.stringify({
  url: location.href,
  txt: (document.body.innerText || '').replace(/\\n{3,}/g, '\\n\\n').slice(0, 700),
  errors: [...document.querySelectorAll('.invalid-feedback, .text-danger, [class*=error]')].map(x => (x.innerText || '').trim()).filter(Boolean).slice(0, 6),
}, null, 1))()`);
log('--- page state ---');
log(state);
ws.close();
process.exit(0);
