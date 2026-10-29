// rp1_state.mjs -- dump the current Dev Center page state (read-only).
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable');

const state = await ev(`(() => {
  const fields = [...document.querySelectorAll('input')].map(i => ({ n: (i.name || i.placeholder || i.id || '?').slice(0, 50), v: (i.value || '').slice(0, 90), t: i.type }))
    .filter(x => x.v || ['lat','lon','width','height','rotation','address'].includes(x.n));
  const labels = [...document.querySelectorAll('label, dt, th, .card-header, h5, h6')].map(l => (l.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 60)).filter(Boolean);
  const vis = (document.body.innerText || '').replace(/\\n{3,}/g, '\\n\\n');
  return JSON.stringify({ url: location.href, fields, labels: labels.slice(0, 40), txt: vis.slice(0, 1800) }, null, 1);
})()`);
console.log(state);
ws.close();
