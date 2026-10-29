// rp1_click.mjs -- click an element by visible text in the logged-in RP1 Dev Center page and
// survey the result. Read-only-ish interaction (one click), used to walk the SPA.
//   node tools/rp1_click.mjs "Cognition"          # click then dump page state
const needle = process.argv[2];
if (!needle) { console.error('usage: node tools/rp1_click.mjs "<text>"'); process.exit(1); }

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

const found = await ev(`(() => {
  const els = [...document.querySelectorAll('a, button, li, span, div')].filter(el => (el.innerText || '').trim() === ${JSON.stringify(needle)} && el.children.length === 0);
  if (!els.length) return 'NOT_FOUND';
  els[els.length - 1].scrollIntoView({ block: 'center' });
  els[els.length - 1].click();
  return 'CLICKED';
})()`);
console.log('click:', found);
if (found === 'CLICKED') {
  await new Promise(r => setTimeout(r, 2500)); // SPA settle
  const state = await ev(`(() => {
    const txt = (document.body?.innerText || '').replace(/\\n{3,}/g, '\\n\\n');
    const forms = [...document.querySelectorAll('input, select, textarea')].map(i => ({ n: i.name || i.id || i.placeholder || i.type || '?', v: (i.value || '').slice(0, 40) }));
    const btns = [...document.querySelectorAll('button, [role=button]')].map(b => (b.innerText || b.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 44)).filter(Boolean);
    return JSON.stringify({ url: location.href, title: document.title, txt: txt.slice(0, 5000), forms, btns: btns.slice(0, 50) }, null, 1);
  })()`);
  console.log(state);
}
ws.close();
