// rp1_scripts.mjs -- list all script URLs loaded by the Dev Center page.
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable');
await send('Page.navigate', { url: 'https://dev.rp1.com/company/137/fabric/create' });
await new Promise(r => setTimeout(r, 3000));
const out = await ev(`(() => { try {
  return JSON.stringify({
    inline: [...document.querySelectorAll('script:not([src])')].map(s => s.textContent.slice(0, 60)),
    srcs: [...document.querySelectorAll('script[src]')].map(s => s.src),
  }, null, 1);
} catch (e) { return 'ERR ' + e; } })()`);
console.log(out);
ws.close();
process.exit(0);
