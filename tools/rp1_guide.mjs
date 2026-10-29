// rp1_guide.mjs -- find the Scene Assembler Guide / FAQ links on the wizard page.
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const links = await ev(`(() => JSON.stringify([...document.querySelectorAll('a')]
  .map(a => (a.innerText || '').trim().slice(0, 40) + ' => ' + a.href)
  .filter(s => /guide|faq|help|doc/i.test(s)).slice(0, 8), null, 1))()`);
console.log(links);
ws.close();
process.exit(0);
