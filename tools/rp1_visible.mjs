// rp1_visible.mjs -- list all VISIBLE buttons/links on the Dev Center page (to find the parcel-picker opener).
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const out = await ev(`(() => {
  const btns = [...document.querySelectorAll('button, [role=button], a')]
    .filter(b => (b.offsetParent || b.getClientRects().length))
    .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 50))
    .filter(Boolean);
  const uniq = [...new Set(btns)];
  return JSON.stringify({ url: location.href, visibleButtons: uniq.slice(0, 50) }, null, 1);
})()`);
console.log(out);
ws.close();
