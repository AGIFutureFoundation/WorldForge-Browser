// rp1_join.mjs -- in the enter.rp1.com tab: click Join World and watch the network for the
// fabric + GLB pull from fly.io.   node tools/rp1_join.mjs
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('enter.rp1.com'));
if (!page) { console.log('no enter.rp1.com tab'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const flyReqs = []; const otherReqs = []; let wreqs = 0;
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.startsWith('ws://') || u.startsWith('wss://')) wreqs++;
    else if (u.includes('worldforge-api.fly.dev')) flyReqs.push(u.slice(0, 130));
    else if (!u.startsWith('data:')) otherReqs.push(u.slice(0, 110));
  }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');

const joined = await ev(`(() => {
  const b = [...document.querySelectorAll('button, [role=button], a, [class*=btn]')]
    .find(x => (x.innerText || '').trim().toLowerCase().includes('join world'));
  if (!b) return 'NOT_FOUND (txt: ' + (document.body.innerText || '').slice(0, 150) + ')';
  b.click();
  return 'CLICKED';
})()`);
console.log('join:', joined);
await new Promise(r => setTimeout(r, 20000)); // world streaming
console.log('--- fly.io fetches (' + flyReqs.length + ') ---');
console.log(flyReqs.join('\n') || '(none)');
console.log('--- other notable requests (last 10 of ' + otherReqs.length + ') ---');
console.log(otherReqs.slice(-10).join('\n'));
console.log('websockets opened:', wreqs);
const state = await ev(`(() => JSON.stringify({ txt: (document.body.innerText || '').slice(0, 250), canvas: [...document.querySelectorAll('canvas')].map(c => c.width + 'x' + c.height) }, null, 1))()`);
console.log('--- tab state ---');
console.log(state);
const shot = await send('Page.captureScreenshot', { format: 'png' });
const { writeFileSync } = await import('node:fs');
writeFileSync('/tmp/rp1-joined.png', Buffer.from(shot.result.data, 'base64'));
console.log('shot: /tmp/rp1-joined.png');
ws.close();
