// rp1_companies.mjs -- list the Dev Center companies with their nav hrefs (read-only).
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

const data = await ev(`(() => {
  // every link/button in the COMPANY nav: text + href (or click handler hints)
  const nav = [...document.querySelectorAll('a, button, [role=button], li, div[class*=company]')]
    .map(el => ({ t: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 50), h: el.href || el.getAttribute('href') || null,
                  cls: (el.className && typeof el.className === 'string') ? el.className.split(' ').slice(0, 3).join('.') : '' }))
    .filter(x => x.t && x.t.length > 1 && x.t.length < 40);
  const seen = new Set(); const out = [];
  for (const x of nav) { const k = x.t + '|' + x.h; if (!seen.has(k)) { seen.add(k); out.push(x); } }
  return JSON.stringify(out.slice(0, 120), null, 1);
})()`);
console.log(data);
ws.close();
