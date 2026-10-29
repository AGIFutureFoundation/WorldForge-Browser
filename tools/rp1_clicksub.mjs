// rp1_clicksub.mjs -- click the last VISIBLE element whose innerText CONTAINS the needle.
//   node tools/rp1_clicksub.mjs "Attach a Fabric"
const needle = process.argv[2];
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable');
const res = await ev(`(() => {
  const cands = [...document.querySelectorAll('button, a, [role=button]')]
    .filter(el => (el.innerText || '').includes(${JSON.stringify(needle)}) && (el.offsetParent || el.getClientRects().length));
  if (!cands.length) return 'NOT_FOUND (visible: ' + [...document.querySelectorAll('button, a')].filter(b => b.offsetParent).map(b => (b.innerText||'').trim().slice(0,30)).filter(Boolean).slice(0,12).join('/') + ')';
  cands[cands.length - 1].scrollIntoView({ block: 'center' });
  cands[cands.length - 1].click();
  return 'CLICKED';
})()`);
console.log('click:', res);
if (res === 'CLICKED') {
  await new Promise(r => setTimeout(r, 3000));
  const state = await ev(`(() => JSON.stringify({
    url: location.href,
    modals: [...document.querySelectorAll('.modal.show, [role=dialog]')].map(m => (m.innerText || '').replace(/\\s+/g, ' ').slice(0, 350)).filter(Boolean),
    inputs: [...document.querySelectorAll('input, select')].filter(i => i.offsetParent || i.getClientRects().length).map(i => ({ n: (i.name || i.id || i.placeholder || i.type || '?').slice(0, 50), v: (i.value || '').slice(0, 40) })).slice(0, 12),
  }, null, 1))()`);
  console.log(state);
}
ws.close();
process.exit(0);
