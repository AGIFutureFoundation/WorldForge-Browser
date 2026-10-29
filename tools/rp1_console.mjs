// rp1_console.mjs -- click Continue on the Attach Fabric wizard and capture JS console
// errors/exceptions for 12s. Log: /tmp/rp1-console.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-console.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `console capture, ${new Date().toISOString()}\n`);

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { log('FATAL'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const errors = []; const reqs = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Runtime.exceptionThrown') errors.push('EXC: ' + (m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text || '').split('\n')[0].slice(0, 220));
  if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(m.params.type)) errors.push(m.params.type.toUpperCase() + ': ' + m.params.args.map(a => a.value ?? a.description ?? JSON.stringify(a.preview?.properties?.map(p => p.value))).join(' ').slice(0, 220));
  if (m.method === 'Network.requestWillBeSent' && !m.params.request.url.startsWith('data:')) reqs.push(m.params.request.method + ' ' + m.params.request.url.slice(0, 120));
  if (m.method === 'Network.loadingFailed') reqs.push('FAILED ' + m.params.errorText + ' ' + (m.params.blocked ? '(blocked)' : ''));
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

await send('Page.navigate', { url: 'https://dev.rp1.com/company/137/fabric/create' });
await sleep(3000);
await ev(`(() => {
  const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('YOURMVSERVERURL'));
  if (inp) { inp.focus(); inp.value = 'https://worldforge-api.fly.dev/fabric/73/1/'; inp.dispatchEvent(new Event('input', { bubbles: true })); }
  const b = [...document.querySelectorAll('button')].filter(x => (x.offsetParent || x.getClientRects().length) && (x.innerText || '').trim() === 'Continue');
  if (b.length) b[0].click();
  return 'clicked ' + (b.length);
})()`);
await sleep(12000);
log('--- console errors/warnings ---');
log(errors.slice(0, 20).join('\n') || '(none)');
log('--- requests (non-data) ---');
log(reqs.slice(-25).join('\n'));
const txt = await ev('(document.body.innerText || "").slice(0, 500)');
log('--- page ---');
log(txt);
ws.close();
process.exit(0);
