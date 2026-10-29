// rp1_goto.mjs -- navigate the logged-in RP1 Dev Center page.
//   node tools/rp1_goto.mjs https://dev.rp1.com/home
const url = process.argv[2];
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable');
await send('Page.navigate', { url });
await new Promise(r => setTimeout(r, 3000));
console.log('URL:   ' + (await ev('location.href')));
console.log('TITLE: ' + (await ev('document.title')));
const txt = await ev('(document.body?.innerText || "").replace(/\\n{3,}/g, "\\n\\n").slice(0, 1200)');
console.log(txt);
ws.close();
