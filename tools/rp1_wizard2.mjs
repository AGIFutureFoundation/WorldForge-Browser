// rp1_wizard2.mjs -- fill the Attach Fabric wizard URL carefully (verify the field holds the full
// value), click Continue, then report the resulting step + any error. Log: /tmp/rp1-wizard2.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-wizard2.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `wizard2, ${new Date().toISOString()}\n`);
const URL_ = 'https://worldforge-api.fly.dev/fabric/73/1/';

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { log('FATAL'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const reqs = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent' && m.params.request.url.includes('worldforge')) reqs.push(m.params.request.url);
  if (m.method === 'Network.responseReceived' && m.params.response.url.includes('worldforge')) reqs.push(`  <- ${m.params.response.status}`);
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

await send('Page.navigate', { url: 'https://dev.rp1.com/company/137/fabric/create' });
await sleep(3000);
const r1 = await ev(`(() => {
  const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('YOURMVSERVERURL'));
  if (!inp) return 'NO_INPUT';
  inp.focus();
  inp.value = ${JSON.stringify(URL_)};
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  // some frameworks need key events to register the typed value
  for (const k of ['keydown', 'keypress', 'keyup']) inp.dispatchEvent(new KeyboardEvent(k, { key: '1', bubbles: true }));
  return 'SET value=' + inp.value;
})()`);
log(`fill: ${r1}`);
await sleep(800);
const r2 = await ev(`(() => {
  const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('YOURMVSERVERURL'));
  const b = [...document.querySelectorAll('button')].filter(x => (x.offsetParent || x.getClientRects().length) && (x.innerText || '').trim() === 'Continue');
  if (b.length) b[0].click();
  return JSON.stringify({ value: inp ? inp.value : null, clicked: b.length });
})()`);
log(`continue: ${r2}`);
await sleep(9000);
const state = await ev(`(() => JSON.stringify({
  url: location.href,
  txt: (document.body.innerText || '').replace(/\\n{3,}/g, '\\n\\n').slice(0, 800),
  errors: [...document.querySelectorAll('.invalid-feedback, .text-danger, [class*=error], .alert')].map(x => (x.innerText || '').trim()).filter(Boolean).slice(0, 8),
}, null, 1))()`);
log(`state: ${state}`);
log(`worldforge requests: ${reqs.join(' | ')}`);
log('--- wizard2 done');
ws.close();
process.exit(0);
