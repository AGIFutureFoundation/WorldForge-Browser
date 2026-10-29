// rp1_region.mjs -- dump the DOM region around a button: its form inputs (with values + visibility).
//   node tools/rp1_region.mjs "Select Parcel"
const needle = process.argv[2];
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
  const btn = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim() === ${JSON.stringify(needle)});
  if (!btn) return 'BUTTON NOT FOUND';
  // walk up to a region big enough to hold the picker form
  let region = btn;
  for (let i = 0; i < 6 && region.parentElement; i++) {
    region = region.parentElement;
    if (region.querySelectorAll('input').length >= 2) break;
  }
  const inputs = [...region.querySelectorAll('input, select')].map(i => ({
    n: (i.name || i.id || i.placeholder || i.type || '?').slice(0, 60), v: (i.value || '').slice(0, 60),
    visible: !!(i.offsetParent || i.getClientRects().length),
  }));
  const btns = [...region.querySelectorAll('button')].map(b => ({
    t: (b.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40),
    visible: !!(b.offsetParent || b.getClientRects().length), disabled: b.disabled,
  })).filter(x => x.t);
  const txt = (region.innerText || '').replace(/\\s+/g, ' ').slice(0, 600);
  return JSON.stringify({ inputs, btns, txt }, null, 1);
})()`);
console.log(out);
ws.close();
