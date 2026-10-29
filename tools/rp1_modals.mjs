// rp1_modals.mjs -- dump open modals/dialogs and the connection banner (read-only).
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
  const modals = [...document.querySelectorAll('.modal.show, [role=dialog], .offcanvas.show, .swal2-container')]
    .map(m => (m.innerText || '').replace(/\\s+/g, ' ').slice(0, 400)).filter(Boolean);
  const banners = [...document.querySelectorAll('.alert, .toast, [class*=disconnected], [class*=reconnect]')]
    .map(a => (a.innerText || '').replace(/\\s+/g, ' ').slice(0, 200)).filter(Boolean);
  const reconnectBtn = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim() === 'Reconnect');
  return JSON.stringify({ modals, banners, reconnectVisible: !!reconnectBtn }, null, 1);
})()`);
console.log(out);
ws.close();
