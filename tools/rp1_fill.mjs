// rp1_fill.mjs -- fill an input by name and click a button in the logged-in RP1 Dev Center.
//   node tools/rp1_fill.mjs "<inputNameOrPlaceholder>" "<value>" "<buttonText>"
const [_, __, inputKey, value, buttonText] = process.argv;

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

const filled = await ev(`(() => {
  const key = ${JSON.stringify(inputKey)};
  let el = [...document.querySelectorAll('input, textarea')].find(i => i.name === key || i.id === key || i.placeholder === key);
  if (!el) el = [...document.querySelectorAll('input, textarea')].find(i => (i.placeholder || '').includes(key));
  if (!el) return 'INPUT_NOT_FOUND: ' + [...document.querySelectorAll('input')].map(i => i.name || i.placeholder).filter(Boolean).slice(0, 12).join(', ');
  el.focus();
  el.value = ${JSON.stringify(value)};
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return 'FILLED';
})()`);
console.log('fill:', filled);

if (buttonText) {
  const clicked = await ev(`(() => {
    const els = [...document.querySelectorAll('button, [role=button], a')].filter(el => (el.innerText || '').trim() === ${JSON.stringify(buttonText)});
    if (!els.length) return 'BUTTON_NOT_FOUND';
    els[els.length - 1].scrollIntoView({ block: 'center' });
    els[els.length - 1].click();
    return 'CLICKED';
  })()`);
  console.log('click:', clicked);
  await new Promise(r => setTimeout(r, 3000)); // let the SPA react
  const state = await ev(`(() => {
    const alert = [...document.querySelectorAll('.alert, [class*=error], [class*=message], [class*=toast]')].map(a => (a.innerText || '').trim()).filter(Boolean).slice(0, 6);
    const vis = [...document.querySelectorAll('button, [role=button]')].map(b => (b.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40)).filter(Boolean).slice(-18);
    return JSON.stringify({ url: location.href, alerts: alert, lastButtons: vis, txt: (document.body.innerText || '').slice(0, 600) }, null, 1);
  })()`);
  console.log(state);
}
ws.close();
