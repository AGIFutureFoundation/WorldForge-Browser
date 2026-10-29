// rp1_step2.mjs -- inspect one half-created company's step2 page (what does it ask for?).
//   node tools/rp1_step2.mjs 195
import fs from 'node:fs';
const cid = process.argv[2] || '195';
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { fs.writeFileSync('/tmp/rp1-step2.txt', 'no page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: `https://dev.rp1.com/company/${cid}/step2` });
await new Promise(r => setTimeout(r, 3000));
const out = await ev(`(() => {
  const inputs = [...document.querySelectorAll('input, select, textarea')].map(i => ({
    n: (i.name || i.id || i.placeholder || i.type || '?').slice(0, 60), v: (i.value || '').slice(0, 50), t: i.type,
    opts: i.tagName === 'SELECT' ? [...i.options].map(o => o.value + ':' + o.text).join(' | ').slice(0, 600) : undefined }));
  const btns = [...document.querySelectorAll('button')].map(b => (b.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 50)).filter(Boolean);
  const txt = (document.body.innerText || '').replace(/\\n{3,}/g, '\\n\\n').slice(0, 1500);
  return JSON.stringify({ url: location.href, inputs, btns: btns.slice(0, 25), txt }, null, 1);
})()`);
fs.writeFileSync('/tmp/rp1-step2.txt', out);
ws.close();
process.exit(0);
