// rp1_verify_fabrics.mjs -- verify the fabric home pages of SmartCiti(137) and Cognition(131):
// fabric URL kept + location + public enter link; then open the SmartCiti enter URL in a new
// tab and capture network requests to worldforge-api.fly.dev (proof RP1 pulls the payload
// from fly.io). NO screenshots (they hang on the heavy WebGL canvas). Log: /tmp/rp1-verify.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-verify.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `verify, ${new Date().toISOString()}\n`);

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
let page = targets.find(t => t.type === 'page' && t.url.includes('dev.rp1.com'));
if (!page) { log('FATAL no dev tab'); process.exit(1); }

const mk = async (wsUrl) => {
  const ws = new WebSocket(wsUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
  let id = 0; const pend = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
  const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
  return { ws, send, ev };
};
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// 1. fabric home states
for (const [name, cid] of [['SmartCiti', 137], ['Cognition', 131], ['Diagnostic', 133], ['Empathic', 132]]) {
  const { ws, send, ev } = await mk(page.webSocketDebuggerUrl);
  await send('Page.enable');
  await send('Page.navigate', { url: `https://dev.rp1.com/company/${cid}/fabric` });
  await sleep(3000);
  const st = await ev(`(() => {
    const inputs = [...document.querySelectorAll('input')].map(i => ({ n: (i.name || i.placeholder || i.id || '').slice(0, 60), v: (i.value || '').slice(0, 100) }))
      .filter(x => x.v && (x.v.includes('worldforge') || x.v.includes('enter.rp1') || x.n === 'lat' || x.n === 'lon' || x.n === 'Latitude' || x.n === 'Longitude'));
    return JSON.stringify({ url: location.href, fields: inputs }, null, 1);
  })()`);
  log(`${name} (${cid}) fabric home: ${st}`);
  ws.close();
}

// 2. visit the SmartCiti fabric in the RP1 browser with network capture (no screenshots)
const enter = await (async () => {
  const { ws, ev } = await mk(page.webSocketDebuggerUrl);
  await ev(`fetch('https://dev.rp1.com/company/137/fabric').then(()=>{})`);
  ws.close();
  return null;
})();
// fetch the SmartCiti public fabric URL from its fabric home
const { ws: wsA, ev: evA } = await mk(page.webSocketDebuggerUrl);
await evA(`location.href = 'https://dev.rp1.com/company/137/fabric'`);
await sleep(3000);
const enterUrl = await evA(`(() => {
  const i = [...document.querySelectorAll('input')].find(x => (x.value || '').includes('enter.rp1.com'));
  return i ? i.value : null;
})()`);
wsA.close();
log(`SmartCiti public fabric URL: ${enterUrl}`);
if (enterUrl) {
  const res = await fetch('http://127.0.0.1:9222/json/new?' + encodeURIComponent(enterUrl), { method: 'PUT' });
  const tab = await res.json();
  await sleep(2500);
  const tabs = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
  const epage = tabs.find(t => t.type === 'page' && (t.targetId === tab.id || t.url.includes('enter.rp1.com')));
  if (!epage) { log('visit tab not found'); process.exit(0); }
  const { ws, send, ev } = await mk(epage.webSocketDebuggerUrl);
  const flyReqs = [];
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.method === 'Network.requestWillBeSent') {
      const u = m.params.request.url;
      if (u.includes('worldforge-api.fly.dev')) flyReqs.push(u.slice(0, 130));
    }
  });
  await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
  // click Join World + skip mic if prompted
  await sleep(4000);
  await ev(`(() => { const b = [...document.querySelectorAll('button, [role=button], a, [class*=btn]')].find(x => ((x.innerText||'').trim().toLowerCase().includes('join world'))); if (b) b.click(); return !!b; })()`);
  await sleep(8000);
  await ev(`(() => { const b = [...document.querySelectorAll('button, [role=button]')].find(x => (x.innerText||'').trim() === 'Skip'); if (b) b.click(); return !!b; })()`);
  await sleep(20000);
  log(`fly.io fetches inside the RP1 browser (${flyReqs.length}):`);
  log(flyReqs.slice(0, 12).join('\n') || '(none captured)');
  const state = await ev(`(() => JSON.stringify({ txt: (document.body.innerText || '').slice(0, 150), canvas: [...document.querySelectorAll('canvas')].map(c => c.width + 'x' + c.height) }))()`);
  log('visit state: ' + state);
  ws.close();
}
log('--- verify done');
process.exit(0);
