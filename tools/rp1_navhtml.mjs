// rp1_navhtml.mjs -- save the companies nav region outerHTML to /tmp/rp1-nav.html (read-only).
import fs from 'node:fs';
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { fs.writeFileSync('/tmp/rp1-nav.html', 'no page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable');
const html = await ev(`(() => {
  // find the nav/section that lists companies (contains "Empathic" and "Diagnostic")
  const cands = [...document.querySelectorAll('nav, aside, ul, div')].filter(el =>
    (el.innerText || '').includes('Empathic') && (el.innerText || '').includes('Parkinsons') && (el.innerText || '').includes('ALS'));
  if (!cands.length) return 'NOT_FOUND: ' + (document.body.innerText || '').slice(0, 300);
  return cands[cands.length - 1].outerHTML.slice(0, 120000);
})()`);
fs.writeFileSync('/tmp/rp1-nav.html', html);
console.log('saved', String(html).length, 'chars');
ws.close();
process.exit(0);
