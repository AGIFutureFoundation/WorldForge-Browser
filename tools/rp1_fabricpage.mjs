// rp1_fabricpage.mjs -- dump the fabric home page details (public URL, location), then click Visit Fabric.
const clickVisit = process.argv.includes('--visit');
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;

const info = await ev(`(() => {
  const inputs = [...document.querySelectorAll('input')].map(i => ({ n: (i.name || i.placeholder || i.id || '?').slice(0, 70), v: (i.value || '').slice(0, 140) })).filter(x => x.v && x.v !== '50' && x.v !== '0');
  return JSON.stringify(inputs, null, 1);
})()`);
console.log('--- fabric page inputs ---');
console.log(info);

if (clickVisit) {
  const clicked = await ev(`(() => {
    const b = [...document.querySelectorAll('button, a')].find(x => (x.innerText || '').trim() === 'Visit Fabric');
    if (!b) return 'NOT_FOUND';
    b.click();
    return 'CLICKED (href=' + (b.href || 'js') + ')';
  })()`);
  console.log('visit:', clicked);
  await new Promise(r => setTimeout(r, 5000));
  const tabs = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
  console.log('--- tabs now ---');
  for (const t of tabs.filter(t => t.type === 'page')) console.log(' -', t.url.slice(0, 110));
}
ws.close();
